from uuid import uuid4
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm4.api.study_design import InterventionalStudyDesign
from usdm4.api.study_version import StudyVersion
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_definition_document import StudyDefinitionDocument
from usdm4.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm4.api.code import Code
from usdm4.api.identifier import StudyIdentifier
from usdm4.api.organization import Organization
from usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem
from usdm4.api.governance_date import GovernanceDate
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.address import Address
from usdm4.api.population_definition import StudyDesignPopulation
from fhir.resources.bundle import Bundle
from fhir.resources.composition import CompositionSection
from usdm4 import USDM4
from usdm4.__info__ import (
    __model_version__ as usdm_version,
)
from usdm4_fhir.__info__ import (
    __system_name__ as SYSTEM_NAME,
    __package_version__ as VERSION,
)
from usdm4_fhir.m11.import_.title_page import TitlePage
from usdm4.builder.builder import Builder
from usdm4.assembler.encoder import Encoder


class ImportPRISM2:
    MODULE = "usdm4_fhir.m11.import_.import_prism2.ImportPRISM2"

    class LogicError(Exception):
        pass

    def __init__(self):
        self._errors: Errors = Errors()
        self._usdm4: USDM4 = USDM4()
        self._builder: Builder = self._usdm4.builder(self._errors)
        self._encoder = Encoder(self._builder, self._errors)
        self._ncs = []
        self._title_page = None
        self._index = 1

    @property
    def errors(self) -> Errors:
        return self._errors

    async def from_message(self, filepath: str) -> Wrapper | None:
        try:
            self._errors.info("Importing FHIR PRISM2")
            data = self._read_file(filepath)
            study = await self._from_fhir(data)
            return Wrapper(
                study=study,
                usdmVersion=usdm_version,
                systemName=SYSTEM_NAME,
                systemVersion=VERSION,
            )
        except Exception as e:
            self._errors.exception(
                "Exception raised parsing FHIR content",
                e,
                KlassMethodLocation(self.MODULE, "from_message"),
            )
            return None

    @property
    def extra(self):
        return {
            "title_page": self._title_page.extra(),
            "amendment": {
                "amendment_details": "",
                "robustness_impact": False,
                "robustness_impact_reason": "",
                "safety_impact": False,
                "safety_impact_reason": "",
            },
            "miscellaneous": {
                "medical_expert_contact": "",
                "sae_reporting_method": "",
                "sponsor_signatory": "",
            },
        }

    async def _from_fhir(self, data: str) -> Wrapper:
        bundle = Bundle.parse_raw(data)
        protocol_document, ncis = self._document(bundle)
        study = await self._study(protocol_document, ncis)
        return study

    def _document(self, bundle):
        self._ncs = []
        protocl_status_code = self._builder.cdisc_code("C85255", "Draft")
        protocl_document_version = self._builder.create(
            StudyDefinitionDocumentVersion,
            {"version": "1", "status": protocl_status_code},
        )
        language: Code = self._builder.iso639_code_or_decode("English")
        doc_type: Code = self._builder.cdisc_code("C70817", "Protocol")
        protocl_document = self._builder.create(
            StudyDefinitionDocument,
            {
                "name": "PROTOCOL V1",
                "label": "M11 Protocol",
                "description": "M11 Protocol Document",
                "language": language,
                "type": doc_type,
                "templateName": "M11",
                "versions": [protocl_document_version],
            },
        )
        # root = self._builder.create(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None})
        # protocl_document_version.contents.append(root)
        ncis = []
        self._index = 1
        for item in bundle.entry[0].resource.section:
            _ = self._section(item, protocl_document_version, ncis)
        self._builder.double_link(
            protocl_document_version.contents, "previousId", "nextId"
        )
        # print(f"DOC: {protocl_document}")
        return protocl_document, ncis

    def _section(
        self,
        section: CompositionSection,
        protocol_document_version: StudyDefinitionDocumentVersion,
        ncis: list,
    ) -> NarrativeContent:
        self._index += 1
        # print(f"SECTION: {section.title}, {section.code.text}")
        section_number = self._get_section_number(section.code.text)
        section_title = section.title
        sn = section_number if section_number else ""
        dsn = True if sn else False
        st = section_title if section_title else ""
        dst = True if st else False
        # print(f"SECTION: sn='{sn}', dsn='{dsn}', st='{st}', dst='{dst}'")
        text = section.text.div if section.text else "&nbsp"
        nci: NarrativeContentItem = self._builder.create(
            NarrativeContentItem, {"name": f"NCI-{self._index}", "text": text}
        )
        nc: NarrativeContent = self._builder.create(
            NarrativeContent,
            {
                "name": f"NC-{self._index}",
                "sectionNumber": sn,
                "displaySectionNumber": dsn,
                "sectionTitle": st,
                "displaySectionTitle": dst,
                "contentItemId": nci.id,
                "childIds": [],
                "previousId": None,
                "nextId": None,
            },
        )
        protocol_document_version.contents.append(nc)
        ncis.append(nci)
        if section.section:
            for item in section.section:
                child_nc: NarrativeContent = self._section(
                    item, protocol_document_version, ncis
                )
                nc.childIds.append(child_nc.id)
        return nc

    def _get_section_number(self, text):
        parts: list[str] = text.split("-")
        return parts[0].replace("section", "") if len(parts) >= 2 else ""

    async def _study(self, protocol_document: StudyDefinitionDocument, ncis: list):
        protocol_document_version = protocol_document.versions[0]
        sections = protocol_document_version.contents
        self._title_page: TitlePage = TitlePage(sections, ncis, self._errors)
        await self._title_page.process()

        # Dates
        sponsor_approval_date_code = self._builder.cdisc_code("C71476", "Approval Date")
        protocol_date_code: Code = self._builder.cdisc_code("C215663", "Effective Date")
        global_code: Code = self._builder.cdisc_code("C68846", "Global")
        global_scope: GeographicScope = self._builder.create(
            GeographicScope, {"type": global_code}
        )
        dates = []
        approval_date: GovernanceDate = self._builder.create(
            GovernanceDate,
            {
                "name": "Approval Date",
                "type": sponsor_approval_date_code,
                "dateValue": self._title_page.sponsor_approval_date,
                "geographicScopes": [global_scope],
            },
        )
        if approval_date:
            dates.append(approval_date)
        protocol_date = self._builder.create(
            GovernanceDate,
            {
                "name": "Protocol Date",
                "type": protocol_date_code,
                "dateValue": self._title_page.version_date,
                "geographicScopes": [global_scope],
            },
        )
        if protocol_date:
            dates.append(protocol_date)

        # Titles
        sponsor_title_code: Code = self._builder.cdisc_code(
            "C207616", "Official Study Title"
        )
        sponsor_short_title_code: Code = self._builder.cdisc_code(
            "C207615", "Brief Study Title"
        )
        acronym_code: Code = self._builder.cdisc_code("C207646", "Study Acronym")
        titles = []
        title = self._builder.create(
            StudyTitle,
            {"text": self._title_page.full_title, "type": sponsor_title_code},
        )
        if title:
            titles.append(title)
        title = self._builder.create(
            StudyTitle, {"text": self._title_page.acronym, "type": acronym_code}
        )
        if title:
            titles.append(title)
        title = self._builder.create(
            StudyTitle,
            {
                "text": self._title_page.short_title,
                "type": sponsor_short_title_code,
            },
        )
        if title:
            titles.append(title)

        # Build
        intervention_model_code: Code = self._builder.cdisc_code(
            "C82639", "Parallel Study"
        )
        sponsor_code: Code = self._builder.cdisc_code(
            "C54149", "Pharmaceutical Company"
        )
        empty_population = self._builder.create(
            StudyDesignPopulation,
            {
                "name": "Study Design Population",
                "label": "Study Population",
                "description": "Empty population details",
                "includesHealthySubjects": True,
            },
        )
        study_design = self._builder.create(
            InterventionalStudyDesign,
            {
                "name": "Study Design",
                "label": "",
                "description": "",
                "rationale": "[Not Found]",
                "model": intervention_model_code,
                "arms": [],
                "studyCells": [],
                "epochs": [],
                "population": empty_population,
                "studyPhase": self._encoder.phase(self._title_page.trial_phase),
            },
        )
        self._title_page.sponsor_address["country"] = (
            self._builder.iso3166_code_or_decode(
                self._title_page.sponsor_address["country"].upper()
            )
        )
        address: Address = self._builder.create(
            Address, self._title_page.sponsor_address
        )
        address.set_text()
        organization: Organization = self._builder.create(
            Organization,
            {
                "name": self._title_page.sponsor_name,
                "label": self._title_page.sponsor_name,
                "type": sponsor_code,
                "identifier": "UNKNOWN",
                "identifierScheme": "UNKNOWN",
                "legalAddress": address,
            },
        )
        identifier: StudyIdentifier = self._builder.create(
            StudyIdentifier,
            {
                "text": self._title_page.sponsor_protocol_identifier,
                "scopeId": organization.id,
            },
        )
        params = {
            "versionIdentifier": self._title_page.version_number,
            "rationale": "Not set",
            "titles": titles,
            "dateValues": dates,
            "studyDesigns": [study_design],
            "documentVersionIds": [protocol_document_version.id],
            "studyIdentifiers": [identifier],
            "organizations": [organization],
            "narrativeContentItems": ncis,
        }
        study_version: StudyVersion = self._builder.create(StudyVersion, params)
        study: Study = self._builder.create(
            Study,
            {
                "id": uuid4(),
                "name": self._title_page.study_name,
                "label": self._title_page.study_name,
                "description": f"FHIR Imported {self._title_page.study_name}",
                "versions": [study_version],
                "documentedBy": [protocol_document],
            },
        )
        return study

    def _read_file(self, full_path: str) -> dict:
        try:
            with open(full_path, "r") as f:
                data = f.read()
                f.close()
                return data
        except Exception as e:
            self._errors.exception(
                "Failed to read FHIR message file",
                e,
                KlassMethodLocation(self.MODULE, "_read_file"),
            )
