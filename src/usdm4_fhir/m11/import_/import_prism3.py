from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.wrapper import Wrapper
from fhir.resources.resource import Resource
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.researchstudy import (
    ResearchStudy,
    ResearchStudyLabel,
    ResearchStudyAssociatedParty,
)
from fhir.resources.organization import Organization
from fhir.resources.extension import Extension
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition, CompositionSection
from fhir.resources.extendedcontactdetail import ExtendedContactDetail
from usdm4 import USDM4
from usdm4_fhir.__info__ import (
    __system_name__ as SYSTEM_NAME,
    __package_version__ as VERSION,
)


class ImportPRISM3:
    MODULE = "usdm4_fhir.m11.import_.import_prism2.ImportPRISM3"
    UDP_BASE = "http://hl7.org/fhir/uv/pharmaceutical-research-protocol"

    class LogicError(Exception):
        pass

    def __init__(self):
        self._errors: Errors = Errors()
        self._usdm4: USDM4 = USDM4()
        self._assembler = self._usdm4.assembler(self._errors)
        self._source_data = {}

    @property
    def errors(self) -> Errors:
        return self._errors

    async def from_message(self, filepath: str) -> Wrapper | None:
        try:
            self._errors.info("Importing FHIR PRISM3")
            data = self._read_file(filepath)
            self._source_data = self._from_fhir(data)
            self._assembler.execute(self._source_data)
            return self._assembler.wrapper(SYSTEM_NAME, VERSION)
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
            "title_page": {
                "compound_codes": "",
                "compound_names": "",
                "amendment_identifier": "",
                "regulatory_agency_identifiers": "",
                # Those below not used?
                "amendment_details": "",
                "amendment_scope": "",
                "manufacturer_name_and_address": "",
                "medical_expert_contact": "",
                "original_protocol": "",
                "sae_reporting_method": "",
                "sponsor_approval_date": "",
                "sponsor_name_and_address": "",
                "sponsor_signatory": "",
            },
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

    def _from_fhir(self, data: str) -> Wrapper:
        try:
            study = None
            bundle = Bundle.parse_raw(data)
            research_study: ResearchStudy = self._extract_from_bundle_type(
                bundle, ResearchStudy.__name__, first=True
            )
            if research_study:
                study = self._study(research_study, bundle)
            else:
                self._errors.warning(
                    "Failed to find ResearchStudy resource in the bundle.",
                    KlassMethodLocation(self.MODULE, "_from_fhir"),
                )
            return study
        except Exception as e:
            self._errors.exception(
                "Exception raised parsing FHIR message",
                e,
                KlassMethodLocation(self.MODULE, "_from_fhir"),
            )
            return None

    def _extract_from_bundle_type(
        self, bundle: Bundle, resource_type: str, first=False
    ) -> list:
        try:
            results = []
            entry: BundleEntry
            for entry in bundle.entry:
                resource: Resource = entry.resource
                if resource.resource_type == resource_type:
                    return resource if first else results.append(resource)
            self._errors.warning(
                "Unable to extract '{resource_type}' by type from the bundle"
            )
            return None if first else results
        except Exception as e:
            self._errors.exception(
                "Exception raised extracting from Bundle",
                e,
                KlassMethodLocation(self.MODULE, "_extract_from_bundle"),
            )
            return None

    def _extract_from_bundle_id(
        self, bundle: Bundle, resource_type: str, id: str
    ) -> list:
        try:
            entry: BundleEntry
            for entry in bundle.entry:
                resource: Resource = entry.resource
                if (resource.resource_type == resource_type) and (
                    f"{resource_type}/{resource.id}" == id
                ):
                    return resource
            self._errors.warning(
                f"Unable to extract '{resource_type}/{id}' by id from the bundle"
            )
            return None
        except Exception as e:
            self._errors.exception(
                "Exception raised extracting from Bundle",
                e,
                KlassMethodLocation(self.MODULE, "_extract_from_bundle"),
            )
            return None

    def _study(self, research_study: ResearchStudy, bundle: Bundle) -> dict:
        try:
            acronym = self._extract_acronym(research_study.label)
            sponsor_identifier = self._extract_sponsor_identifier(
                research_study.identifier
            )
            sponsor = self._extract_sponsor(research_study.associatedParty, bundle)
            sections = self._extract_sections(research_study.extension, bundle)
            result = {
                "identification": {
                    "titles": {
                        "official": research_study.title,
                        "acronym": acronym,
                        "brief": self._extract_brief_title(research_study.label),
                    },
                    "identifiers": [
                        {
                            "identifier": sponsor_identifier,
                            "scope": sponsor,
                        }
                    ],
                },
                "compounds": {
                    "compound_codes": "",  # <<<<<
                    "compound_names": "",  # <<<<<
                },
                "amendments_summary": {
                    "amendment_identifier": "",  # <<<<<
                    "amendment_scope": "",  # <<<<<
                    "amendment_details": "",  # <<<<<
                },
                "study_design": {
                    "label": "Study Design 1",
                    "rationale": "Not set",
                    "trial_phase": self._extract_phase(research_study.phase),
                },
                "study": {
                    "sponsor_approval_date": research_study.date.isoformat()
                    if research_study.date
                    else "",
                    "version_date": "",  # <<<<<
                    "version": research_study.version,
                    "rationale": "Not set",
                    "name": {
                        "acronym": acronym,
                        "identifier": sponsor_identifier,
                        "compound_code": "",  # "compund code", <<<<<
                    },
                    "confidentiality": self._extract_confidentiality_statement(
                        research_study.extension
                    ),
                    "original_protocol": self._extract_original_protocol(
                        research_study.extension
                    ),
                },
                "other": {
                    "regulatory_agency_identifiers": "",  # <<<<<
                },
                "document": {
                    "document": {
                        "label": "Protocol Document",
                        "version": research_study.version,
                        "status": "Final",  # @todo
                        "template": "M11",
                        "version_date": research_study.date.isoformat() if research_study.date else "",
                    },
                    "sections": sections,
                },
                "population": {
                    "label": "Default population",
                    "inclusion_exclusion": {
                        "inclusion": [],
                        "exclusion": [],
                    },
                },
                "amendments": [],
            }
            self._add_regualtory_identifer(self._extract_fda_ind_identifier(research_study.identifier), "fda", result)
            self._add_regualtory_identifer(self._extract_ema_identifier(research_study.identifier), "ema", result)
            self._add_regualtory_identifer(self._extract_nct_identifier(research_study.identifier), "ct.gov", result)
            print(f"FHIR IDs: {result["identification"]["identifiers"]}")
            return result
        except Exception as e:
            self._errors.exception(
                "Exception raised assembling study information",
                e,
                KlassMethodLocation(self.MODULE, "__study"),
            )
            return None

    def _add_regualtory_identifer(self, identifier: str, type: str, result) -> None:
        if identifier:
            params = {
                "identifier": identifier,
                "scope": {
                    "standard": type,
                }
            }
            result["identification"]["identifiers"].append(params)

    def _extract_sponsor(self, assciated_parties: list, bundle: Bundle) -> dict:
        party: ResearchStudyAssociatedParty
        for party in assciated_parties:
            if self._is_sponsor(party.role):
                organization: Organization = self._extract_from_bundle_id(
                    bundle, "Organization", party.party.reference
                )
                if organization:
                    extended_contact: ExtendedContactDetail = organization.contact[0]
                    # print(f"Address source: {extended_contact.address.__dict__}")
                    address = self._to_address(extended_contact.address.__dict__)
                    # print(f"Address dict: {address}")
                    return {
                        "non_standard": {
                            "type": "pharma",
                            "description": "The sponsor organization",
                            "label": organization.name,
                            "identifier": "UNKNOWN",
                            "identifierScheme": "UNKNOWN",
                            "legalAddress": address,
                        }
                    }
        self._errors.warning(
            "Unable to extract sponsor details from associated parties"
        )
        return {
            "non_standard": {
                "type": "pharma",
                "description": "The sponsor organization",
                "label": "Unknown",
                "identifier": "UNKNOWN",
                "identifierScheme": "UNKNOWN",
                "legalAddress": None,
            }
        }

    def _to_address(self, address: dict) -> dict | None:
        keys = [
            ("city", "city"),
            ("country", "country"),
            ("district", "district"),
            ("line", "lines"),
            ("postalCode", "postalCode"),
            ("state", "state"),
            ("text", "text"),
        ]
        result = {}
        valid = False
        for k in keys:
            if address[k[0]]:
                # print(f"KEY: {k}")
                result[k[1]] = address[k[0]]
                valid = True
        # print(f"ADDR: {valid}, {result}")
        return result if valid else None

    def _is_sponsor(self, role: CodeableConcept) -> bool:
        try:
            code: Coding = role.coding
            return code[0].code == "sponsor"
        except Exception as e:
            print(f"IS SPONSOR EXP: {e}")
            return False

    def _extract_phase(self, phase: CodeableConcept) -> str:
        if phase.coding:
            coding: Coding = phase.coding[0]
            return coding.display
        self._errors.warning(
            "Failed ot detect phase in ResearchStudy resource",
            KlassMethodLocation(self.MODULE, "_extract_phase"),
        )
        return ""

    def _extract_sponsor_identifier(self, identifiers: list) -> str:
        return self._extract_identifier(identifiers, "C132351", "code")

    def _extract_fda_ind_identifier(self, identifiers: list) -> str:
        return self._extract_identifier(identifiers, "C218685", "code")

    def _extract_ema_identifier(self, identifiers: list) -> str:
        return self._extract_identifier(identifiers, "C218684", "code")

    def _extract_nct_identifier(self, identifiers: list) -> str:
        return self._extract_identifier(identifiers, "C172240", "code")

    def _extract_identifier(
        self, identifiers: list, type: str, attribute_name: str
    ) -> str | None:
        if identifiers:
            item: Identifier
            for item in identifiers:
                coding: CodeableConcept
                if coding := item.type.coding[0]:
                    value = getattr(coding, attribute_name)
                    if value == type:
                        self._errors.info(
                            f"Extracted identifier of type '{coding.display}': '{item.value}'"
                        )
                        return item.value
        self._errors.warning(f"Failed to extract identifier of type '{type}'")
        return None

    def _extract_acronym(self, labels) -> str:
        return self._extract_label(labels, "C207646")

    def _extract_brief_title(self, labels) -> str:
        return self._extract_label(labels, "C207615")

    def _extract_label(self, labels, type) -> str:
        if labels:
            label: ResearchStudyLabel
            for label in labels:
                if label.type.coding[0].code == type:
                    return label.value
        return ""

    def _extract_sections(self, extensions: list, bundle: Bundle) -> dict:
        results = []
        references = self._extract_narrative_references(extensions)
        for reference in references:
            composition: Composition = self._extract_from_bundle_id(
                bundle, "Composition", reference
            )
            results += self._extract_section(composition.section)
        return results

    def _extract_section(self, sections: list[CompositionSection]):
        results = []
        section: CompositionSection
        for section in sections:
            results.append(
                {
                    "section_number": self._get_section_number(section.code.text),
                    "section_title": section.title,
                    "text": section.text.div if section.text else "",
                }
            )
            if section.section:
                results += self._extract_section(section.section)
        return results

    def _get_section_number(self, text):
        parts: list[str] = text.split("-")
        return parts[0].replace("section", "") if len(parts) >= 2 else ""

    def _extract_narrative_references(self, extensions: list) -> list:
        results = []
        item: Extension
        for item in extensions:
            if (
                item.url
                == "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/narrative-elements"
            ):
                results.append(item.valueReference.reference)
        return results

    def _extract_confidentiality_statement(self, extensions: list) -> str:
        ext = self._extract_extension(
            extensions,
            "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
        )
        return ext.valueString if ext else ""

    def _extract_original_protocol(self, extensions: list) -> str:
        ext = self._extract_extension(
            extensions,
            f"{self.UDP_BASE}/study-amendment",
        )
        return ext.valueCoding.display if ext else "NO"

    def _extract_extension(self, extensions: list, url: str) -> Extension:
        item: Extension
        for item in extensions:
            if item.url == url:
                return item
        return None

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
