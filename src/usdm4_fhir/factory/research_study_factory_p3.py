from uuid import uuid4
from usdm4.api.study import Study as USDMStudy
from usdm4.api.study_version import StudyVersion as USDMStudyVersion
from usdm4.api.study_title import StudyTitle
from fhir.resources.researchstudy import ResearchStudy
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.coding_factory import CodingFactory
from usdm4_fhir.factory.label_type_factory import LabelTypeFactory
from usdm4_fhir.factory.organization_factory import OrganizationFactory
from usdm4_fhir.factory.associated_party_factory import AssociatedPartyFactory


class ResearchStudyFactoryP3(BaseFactory):
    NCI_CODE_SYSTEM = "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl"
    UDP_BASE = "http://hl7.org/fhir/uv/pharmaceutical-research-protocol"
    PROTOCOL_AMENDMENT_BASE = "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/protocol-amendment"

    def __init__(self, study: USDMStudy, extra: dict = {}):
        try:
            self._title_page = extra["title_page"]
            self._version: USDMStudyVersion = study.first_version()
            self._study_design = self._version.studyDesigns[0]
            self._document = study.documentedBy[0].versions[0]
            self._organizations: dict = self._version.organization_map()
            self._resources: list[BaseFactory] = []

            # Set Profile meta data
            meta = {
                "profile": [
                    "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/m11-research-study-profile"
                ]
            }

            # Base instance
            self.item = ResearchStudy(
                id=str(uuid4()),
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
            if cs := self._version.confidentiality_statement():
                ext = ExtensionFactory(
                    url="http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
                    valueString=cs
                )
                self.item.extension.append(ext.item)

            # Full Title
            self.item.title = self._version.official_title_text()

            # Trial Acronym and Short Title
            acronym: StudyTitle = self._version.acronym()
            if acronym:
                if acronym.text:
                    self.item.label.append(
                        LabelTypeFactory(usdm_code=acronym.type, text=acronym.text).item
                    )
            st: StudyTitle = self._version.short_title()
            if st:
                if st.text:
                    self.item.label.append(
                        LabelTypeFactory(usdm_code=st.type, text=st.text).item
                    )

            # Sponsor Identifier
            identifier = self._version.sponsor_identifier()
            if identifier:
                identifier_type = CodingFactory(
                    system=self.NCI_CODE_SYSTEM,
                    code="C132351",
                    display="Sponsor Protocol Identifier",
                )
                self.item.identifier.append(
                    {
                        "type": {"coding": [identifier_type.item]},
                        "system": "https://d4k.dk/sponsor-identifier",
                        "value": identifier.text,
                    }
                )

            # Original Protocol - No implementation details currently
            original_code = CodingFactory(
                system=self.NCI_CODE_SYSTEM, code="C49487", display="No"
            )
            if self._version.original_version():
                original_code.item.code = "C49488"
                original_code.item.display = "Yes"
            ext = ExtensionFactory(
                **{
                    "url": f"{self.UDP_BASE}/study-amendment",
                    "valueCoding": original_code.item,
                }
            )
            self.item.extension.append(ext.item)

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
            if self._title_page["amendment_identifier"]:
                identifier_code = CodingFactory(
                    system=self.NCI_CODE_SYSTEM,
                    code="C218477",
                    display="Amendment Identifier",
                )
                self.item.identifier.append(
                    {
                        "type": {"coding": [identifier_code.item]},
                        "system": "https://example.org/amendment-identifier",
                        "value": self._title_page["amendment_identifier"],
                    }
                )

            # Amendment Scope
            the_scope = (
                self._title_page["amendment_scope"]
                if self._title_page["amendment_scope"]
                else "Global"
            )
            scope = ExtensionFactory(
                **{
                    "url": "scope",
                    "valueCode": the_scope,
                }
            )
            ext = ExtensionFactory(
                **{
                    "url": f"{self.PROTOCOL_AMENDMENT_BASE}",
                    "extension": [scope.item],
                }
            )
            self.item.extension.append(ext.item)

            # Compound Codes - No implementation details currently
            # if self._title_page["compound_codes"]:
            #     params = {
            #         "id": str(uuid4()),
            #         "name": ["something"],
            #         "identifier": [
            #             {
            #                 "system": "https://example.org/sponsor-identifier",
            #                 "value": self._title_page["compound_codes"],
            #             }
            #         ],
            #     }
            #     medicinal_product = MedicinalProductDefinitionFactory(**params)
            #     self._resources.append(medicinal_product)

            # Compound Names - No implementation details currently
            # _ = self._title_page["compound_names"]

            # Trial Phase
            phase = self._study_design.phase()
            phase_code = CodingFactory(
                system="http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
                code=phase.code,
                display=phase.decode,
            )
            self.item.phase = CodeableConceptFactory(
                coding=[phase_code.item], text=phase.decode
            ).item

            # Sponsor Name and Address
            sponsor = self._version.sponsor()
            org = OrganizationFactory(sponsor)
            ap = AssociatedPartyFactory(
                party={"reference": f"Organization/{org.item.id}"},
                role_code="sponsor",
                role_display="sponsor",
            )
            self.item.associatedParty.append(ap.item)
            self._resources.append(org)

            # Co-sponsor Name and Address

            # Local-sponsor Name and Address

            # Device Manufacturer Name and Address

            # Regulatory Agency and CT Registry Identifiers
            identifiers = self._version.regulatory_identifiers()
            identifiers += self._version.registry_identifiers()
            for identifier in identifiers:
                org = identifier.scoped_by(self._organizations)
                if org.name == "FDA":
                    identifier_type = CodingFactory(
                        system=self.NCI_CODE_SYSTEM,
                        code="C218685",
                        display="FDA IND Number",
                    )
                    self.item.identifier.append(
                        {
                            "type": {"coding": [identifier_type.item]},
                            "system": "https://example.org/fda-ind-identifier",
                            "value": identifier.text,
                        }
                    )
                elif org.name == "CT.GOV":
                    identifier_type = CodingFactory(
                        system=self.NCI_CODE_SYSTEM,
                        code="C172240",
                        display="NCT Number",
                    )
                    self.item.identifier.append(
                        {
                            "type": {"coding": [identifier_type.item]},
                            "system": "https://example.org/fda-ind-identifier",
                            "value": identifier.text,
                        }
                    )
                elif org.name == "EMA":
                    identifier_type = CodingFactory(
                        system=self.NCI_CODE_SYSTEM,
                        code="C218684",
                        display="EU CT Number",
                    )
                    self.item.identifier.append(
                        {
                            "type": {"coding": [identifier_type.item]},
                            "system": "https://example.org/fda-ind-identifier",
                            "value": identifier.text,
                        }
                    )
                else:
                    # Ignore for the moment
                    pass

            # # Sponsor Approval
            # g_date: GovernanceDate = self._version.approval_date()
            # date_str = (
            #     g_date.dateValue
            #     if g_date
            #     else datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            # )
            # status = ProgressStatusFactory(
            #     value=date_str,
            #     state_code="sponsor-approved",
            #     state_display="sponsor apporval date",
            # )
            # self.item.progressStatus.append(status.item)

            # # Sponsor Signatory
            # ap = AssociatedPartyFactory(party={'value': self._title_page['sponsor_signatory']}, role_code='sponsor-signatory', role_display='sponsor signatory')
            # self.item.associatedParty.append(ap.item)

            # # Medical Expert Contact
            # ap = AssociatedPartyFactory(party={'value': self._title_page['medical_expert_contact']}, role_code='medical-expert', role_display='medical-expert')
            # self.item.associatedParty.append(ap.item)

        except Exception as e:
            self.item = None
            self.handle_exception(e)

    @property
    def resources(self) -> list[BaseFactory]:
        return self._resources
