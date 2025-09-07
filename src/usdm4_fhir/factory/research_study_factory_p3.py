import datetime
from usdm4.api.study import Study as USDMStudy
from usdm4.api.study_version import StudyVersion as USDMStudyVersion
from usdm4.api.governance_date import GovernanceDate
from fhir.resources.researchstudy import ResearchStudy
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.coding_factory import CodingFactory
from usdm4_fhir.factory.organization_factory import OrganizationFactory
from usdm4_fhir.factory.associated_party_factory import AssociatedPartyFactory
from usdm4_fhir.factory.progress_status_factory import ProgressStatusFactory
from usdm4_fhir.factory.label_type_factory import LabelTypeFactory


class ResearchStudyFactoryP3(BaseFactory):
    def __init__(self, study: USDMStudy, extra: dict = {}):
        try:
            self._title_page = extra["title_page"]
            # self._miscellaneous = extra['miscellaneous']
            # self._amendment = extra['amendment']
            self._version: USDMStudyVersion = study.first_version()
            self._study_design = self._version.studyDesigns[0]
            self._organizations: dict = self._version.organization_map()

            # Set Profile meta data
            meta = {
                "profile": [
                    "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/m11-research-study-profile"
                ]
            }
            
            # Base instance
            self.item = ResearchStudy(
                id=f"{self._version.sponsor_identifier_text()}-ResearchStudy",
                meta=meta,
                status="active",
                identifier=[],
                extension=[],
                label=[],
                associatedParty=[],
                progressStatus=[],
                objective=[],
                comparisonGroup=[],
                outcomeMeasure=[],
                protocol=[],
            )

            # Sponsor Confidentiality Statememt
            if self._title_page["sponsor_confidentiality"]:
                ext = ExtensionFactory(
                    **{
                        "url": "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
                        "valueString": self._title_page["sponsor_confidentiality"],
                    }
                )
                self.item.extension.append(ext.item)

            # Full Title
            self.item.title = (
                self._version.official_title_text()
            )  # self._get_title('Official Study Title').text

            # Trial Acronym
            acronym = self._version.acronym()  # self._get_title('Study Acronym')
            if acronym:
                self.item.label.append(
                    LabelTypeFactory(usdm_code=acronym.type, text=acronym.text).item
                )

            # Sponsor Protocol Identifier
            for identifier in self._version.studyIdentifiers:
                org = identifier.scoped_by(self._organizations)
                identifier_cc = CodeableConceptFactory(text=org.type.decode)
                self.item.identifier.append(
                    {
                        "type": identifier_cc.item,
                        "system": "https://example.org/sponsor-identifier",
                        "value": identifier.text,
                    }
                )

            # Original Protocol - No implementation details currently
            # x = self._title_page['original_protocol']

            # Version Number
            self.item.version = (
                self._version.versionIdentifier
                if self._version.versionIdentifier
                else "1"
            )

            # Version Date
            date_value = self._version.approval_date_value()
            if date_value:
                self.item.date = date_value

            # Amendment Identifier
            identifier_code = CodeableConceptFactory(text="Amendment Identifier")
            self.item.identifier.append(
                {
                    "type": identifier_code.item,
                    "system": "https://example.org/amendment-identifier",
                    "value": self._title_page["amendment_identifier"],
                }
            )

            # Amendment Scope - Part of Amendment

            # Compound Codes - No implementation details currently
            # _ = self._title_page["compound_codes"]

            # Compound Names - No implementation details currently
            # _ = self._title_page["compound_names"]

            # Trial Phase
            phase = self._study_design.phase()
            phase_code = CodingFactory(
                system=phase.codeSystem,
                version=phase.codeSystemVersion,
                code=phase.code,
                display=phase.decode,
            )
            self.item.phase = CodeableConceptFactory(
                coding=[phase_code.item], text=phase.decode
            ).item

            # Short Title
            title = self._version.short_title()  # self._get_title('Brief Study Title')
            self.item.label.append(
                LabelTypeFactory(usdm_code=title.type, text=title.text).item
            )

            # Sponsor Name and Address
            sponsor = self._version.sponsor()
            print(f"SPONSOR: {sponsor}")
            org = OrganizationFactory(sponsor)
            # self._entries.append({'item': org.item, 'url': 'https://www.example.com/Composition/1234D'})
            ap = AssociatedPartyFactory(
                party={"reference": f"Organization/{self.fix_id(org.item.id)}"},
                role_code="sponsor",
                role_display="sponsor",
            )
            self.item.associatedParty.append(ap.item)

            # Manufacturer Name and Address
            # x = self._title_page['manufacturer_name_and_address']

            # Regulatory Agency Identifiers, see above
            # x = self._title_page['regulatory_agency_identifiers']

            # Sponsor Approval
            g_date: GovernanceDate = self._version.approval_date()
            date_str = (
                g_date.dateValue
                if g_date
                else datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            )
            status = ProgressStatusFactory(
                value=date_str,
                state_code="sponsor-approved",
                state_display="sponsor apporval date",
            )
            self.item.progressStatus.append(status.item)

            # # Sponsor Signatory
            # ap = AssociatedPartyFactory(party={'value': self._title_page['sponsor_signatory']}, role_code='sponsor-signatory', role_display='sponsor signatory')
            # self.item.associatedParty.append(ap.item)

            # # Medical Expert Contact
            # ap = AssociatedPartyFactory(party={'value': self._title_page['medical_expert_contact']}, role_code='medical-expert', role_display='medical-expert')
            # self.item.associatedParty.append(ap.item)

        except Exception as e:
            self.item = None
            self.handle_exception(e)
