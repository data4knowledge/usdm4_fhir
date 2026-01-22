from uuid import uuid4
from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.study import Study as USDMStudy
from usdm4.api.study_version import StudyVersion as USDMStudyVersion
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_amendment import StudyAmendment
from usdm4.api.study_amendment_impact import StudyAmendmentImpact
from fhir.resources.researchstudy import ResearchStudy
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory, Extension
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.coding_factory import CodingFactory
from usdm4_fhir.factory.label_type_factory import LabelTypeFactory
from usdm4_fhir.factory.organization_factory import OrganizationFactory
from usdm4_fhir.factory.associated_party_factory import AssociatedPartyFactory


class ResearchStudyFactoryP3(BaseFactory):
    MODULE = "usdm4_fhir.factory.research_study_factory_p3.ResearchStudyFactoryP3"
    NCI_CODE_SYSTEM = "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl"
    UDP_BASE = "http://hl7.org/fhir/uv/pharmaceutical-research-protocol"

    def __init__(self, study: USDMStudy, errors: Errors, extra: dict = {}):
        try:
            super().__init__(errors, **{})
            self._title_page = extra["title_page"]
            self._version: USDMStudyVersion = study.first_version()
            self._first_amendment: StudyAmendment = self._version.first_amendment()
            self._study_design = self._version.studyDesigns[0]
            self._document = study.documentedBy[0].versions[0]
            self._organizations: dict = self._version.organization_map()
            self._resources: list[BaseFactory] = []

            # Set Profile meta data
            meta = {
                "profile": [
                    f"{self.UDP_BASE}/StructureDefinition/m11-research-study-profile"
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
                    errors=self._errors,
                    url="http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
                    valueString=cs,
                )
                self.item.extension.append(ext.item)

            # Full Title
            self.item.title = self._version.official_title_text()

            # Trial Acronym and Short Title
            acronym: StudyTitle = self._version.acronym()
            if acronym:
                if acronym.text:
                    self.item.label.append(
                        LabelTypeFactory(
                            errors=self._errors,
                            usdm_code=acronym.type,
                            text=acronym.text,
                        ).item
                    )
            st: StudyTitle = self._version.short_title()
            if st:
                if st.text:
                    self.item.label.append(
                        LabelTypeFactory(
                            errors=self._errors, usdm_code=st.type, text=st.text
                        ).item
                    )

            # Sponsor Identifier
            identifier = self._version.sponsor_identifier()
            if identifier:
                identifier_type = CodingFactory(
                    errors=self._errors,
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

            # Original Protocol
            original_code = CodingFactory(
                errors=self._errors,
                system=self.NCI_CODE_SYSTEM,
                code="C49487",
                display="No",
            )
            if self._version.original_version():
                original_code.item.code = "C49488"
                original_code.item.display = "Yes"
            ext = ExtensionFactory(
                errors=self._errors,
                url=f"{self.UDP_BASE}/study-amendment",
                valueCoding=original_code.item,
            )
            if ext.item:
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

            # Amendment Identifier and Scope
            if not self._version.original_version():
                self._errors.info("Amendment present based on original protocol value")
                if self._first_amendment:
                    self._errors.info(
                        f"First amendment detected '{self._first_amendment.number}'"
                    )
                    if self._first_amendment.number:
                        identifier_code = CodingFactory(
                            errors=self._errors,
                            system=self.NCI_CODE_SYSTEM,
                            code="C218477",
                            display="Amendment Identifier",
                        )
                        self.item.identifier.append(
                            {
                                "type": {"coding": [identifier_code.item]},
                                "system": "https://d4k.dk/amendment-identifier",
                                "value": self._first_amendment.number,
                            }
                        )
                        ext = self._create_amendment()
                        if ext:
                            self.item.extension.append(ext.item)
                    else:
                        self._errors.error(
                            "Empty identifier for first amendment",
                            KlassMethodLocation(self.MODULE, "__init__"),
                        )
                else:
                    self._errors.error(
                        "Could not find first amendment",
                        KlassMethodLocation(self.MODULE, "__init__"),
                    )
            else:
                self._errors.error(
                    "No amendment, original protocol",
                    KlassMethodLocation(self.MODULE, "__init__"),
                )
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
                errors=self._errors,
                system="http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
                code=phase.code,
                display=phase.decode,
            )
            self.item.phase = CodeableConceptFactory(
                errors=self._errors, coding=[phase_code.item], text=phase.decode
            ).item

            # Sponsor Name and Address
            sponsor = self._version.sponsor()
            org = OrganizationFactory(errors=self._errors, organization=sponsor)
            ap = AssociatedPartyFactory(
                errors=self._errors,
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
                        errors=self._errors,
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
                        errors=self._errors,
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
                        errors=self._errors,
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
            self.handle_exception(self.MODULE, "__init__", e)

    @property
    def resources(self) -> list[BaseFactory]:
        return self._resources

    def _create_amendment(self) -> ExtensionFactory:
        if len(self._version.amendments) == 0:
            return None

        # Get source amendment and create the overall FHIR extension
        source_amendment: StudyAmendment = self._version.amendments[0]
        amendment_factory: ExtensionFactory = ExtensionFactory(
            errors=self._errors,
            url=f"{self.UDP_BASE}/StructureDefinition/protocol-amendment",
            extension=[],
        )
        amendment: Extension = amendment_factory.item

        # Scope
        self._add_scope(amendment, source_amendment)

        # Rationale
        self._add_amendment_extension(amendment, "rationale", source_amendment.summary)

        # Identifier / Number
        self._add_amendment_extension(
            amendment, "amendmentNumber", source_amendment.number
        )

        # Primary and secondary reasons
        self._add_primary_and_secondary(amendment, source_amendment)

        # Impacts
        self._add_impacts(amendment, source_amendment)

        # Changes
        self._add_changes(amendment, source_amendment)

        # Return extension
        return amendment_factory

    def _add_impacts(
        self, amendment: Extension, source_amendment: StudyAmendment
    ) -> None:
        impact: StudyAmendmentImpact = next(
            (x for x in source_amendment.impacts if x.type.code == "C123456"), None
        )
        if impact and impact.isSubstantial:
            sis = ExtensionFactory(
                errors=self._errors, url="substantialImpactSafety", valueCode="C49488"
            )
            sisc = ExtensionFactory(
                errors=self._errors,
                url="substantialImpactSafetyComment",
                valueString=impact.text,
            )
            if sis and sisc:
                amendment.append(sis)
                amendment.append(sisc)
        impact: StudyAmendmentImpact = next(
            (x for x in source_amendment.impacts if x.type.code == "C123456"), None
        )
        if impact and impact.isSubstantial:
            sir = ExtensionFactory(
                errors=self._errors,
                url="substantialImpactReliability",
                valueCode="C49488",
            )
            sirc = ExtensionFactory(
                errors=self._errors,
                url="ubstantialImpactReliabilityComment",
                valueString=impact.text,
            )
            if sir and sirc:
                amendment.append(sir)
                amendment.append(sirc)

    def _add_changes(
        self, amendment: Extension, source_amendment: StudyAmendment
    ) -> None:
        for change in source_amendment.changes:
            change_ext = ExtensionFactory(
                errors=self._errors,
                url="http://hl7.org/fhir/uv/clinical-study-protocol/StructureDefinition/protocol-amendment-detail",
                extension=[],
            )
            self._add_amendment_extension(change_ext.item, "detail", change.summary)
            self._add_amendment_extension(
                change_ext.item, "rationale", change.rationale
            )
            if change.changedSections:
                c_code, display = self._section_map(
                    change.changedSections[0].sectionNumber
                )
                code = CodingFactory(
                    errors=self._errors,
                    system="http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
                    code=c_code,
                    display=display,
                )
                cc = CodeableConceptFactory(errors=self._errors, coding=[code.item])
                ext: ExtensionFactory = ExtensionFactory(
                    errors=self._errors, url="section", valueCodeableConcept=cc.item
                )
                change_ext.item.extension.append(ext.item)
            else:
                self._errors.warning(
                    f"No changed sections for change '{change.summary}'",
                    KlassMethodLocation(self.MODULE, "_add_changes"),
                )
            amendment.extension.append(change_ext.item)

    def _section_map(self, section_number: str) -> tuple[str, str]:
        ct_map = {
            "1": {"code": "C217342", "display": "Section 1"},
            "2": {"code": "C217343", "display": "Section 2"},
            "3": {"code": "C217344", "display": "Section 3"},
            "4": {"code": "C217345", "display": "Section 4"},
            "5": {"code": "C217346", "display": "Section 5"},
            "6": {"code": "C217347", "display": "Section 6"},
            "7": {"code": "C217348", "display": "Section 7"},
            "8": {"code": "C217349", "display": "Section 8"},
            "9": {"code": "C217350", "display": "Section 9"},
            "10": {"code": "C217351", "display": "Section 10"},
            "11": {"code": "C217352", "display": "Section 11"},
            "12": {"code": "C217353", "display": "Section 12"},
            "13": {"code": "C217354", "display": "Section 13"},
            "14": {"code": "C217355", "display": "Section 14"},
            "Title Page": {"code": "C217356", "display": "Section Title Page"},
            "Amendment Details": {
                "code": "C217357",
                "display": "Section Amendment Details",
            },
        }
        parts = section_number.split(".")
        key = parts[0]
        result = (
            (ct_map[key]["code"], ct_map[key]["display"])
            if key in ct_map
            else ("Uknown", "Unknown")
        )
        self._errors.info(
            f"Secton map result '{section_number}' -> {result}",
            KlassMethodLocation(self.MODULE, "_section_map"),
        )
        return result

    def _add_scope(
        self, amendment: Extension, source_amendment: StudyAmendment
    ) -> None:
        the_scope = (
            self._title_page["amendment_scope"]
            if self._title_page["amendment_scope"]
            else "Global"
        )
        scope = ExtensionFactory(errors=self._errors, url="scope", valueCode=the_scope)
        if scope:
            amendment.extension.append(scope.item)
        else:
            self._errors.error(
                f"Failed to create 'scope' extension with value '{the_scope}'",
                KlassMethodLocation(self.MODULE, "_add_scope"),
            )

    def _add_primary_and_secondary(
        self, amendment: Extension, source_amendment: StudyAmendment
    ) -> None:
        code = CodingFactory(
            errors=self._errors,
            system="http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
            code=source_amendment.primaryReason.code.code,
            display=source_amendment.primaryReason.code.decode,
        )
        primary = CodeableConceptFactory(errors=self._errors, coding=[code.item])
        ext: ExtensionFactory = ExtensionFactory(
            errors=self._errors, url="primaryReason", valueCodeableConcept=primary.item
        )
        if ext.item:
            amendment.extension.append(ext.item)
            code = CodingFactory(
                errors=self._errors,
                system="http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
                code=source_amendment.secondaryReasons[0].code.code,
                display=source_amendment.secondaryReasons[0].code.decode,
            )
            secondary = CodeableConceptFactory(errors=self._errors, coding=[code.item])
            ext: ExtensionFactory = ExtensionFactory(
                errors=self._errors,
                url="secondaryReason",
                valueCodeableConcept=secondary.item,
            )
            if ext.item:
                amendment.extension.append(ext.item)
            else:
                self._errors.error(
                    f"Failed to create 'secondaryReason' extension with value '{source_amendment.secondaryReasons[0]}'",
                    KlassMethodLocation(self.MODULE, "_add_primary_and_secondary"),
                )
        else:
            self._errors.error(
                f"Failed to create 'primaryReason' extension with value '{source_amendment.primaryReason}'",
                KlassMethodLocation(self.MODULE, "_add_primary_and_secondary"),
            )

    def _add_amendment_extension(
        self, amendment: Extension, url: str, value: str
    ) -> None:
        if value:
            ext: ExtensionFactory = ExtensionFactory(
                errors=self._errors, url=url, valueString=value
            )
            if ext.item:
                amendment.extension.append(ext.item)
        else:
            self._errors.warning(
                f"Failed to create amendment extension '{url}' with empty value '{value}'",
                KlassMethodLocation(self.MODULE, "_add_amendment_extension"),
            )

    # First cut of amendment code. Example structure
    # ==============================================

    # AMENDMENT ENROLLMENT
    # {
    #   "extension" : [
    #     {
    #       "url" : "scope",
    #       "valueCode" : "C217026"
    #     },
    #     {
    #       "url" : "country",
    #       "valueCode" : "DE"
    #     },
    #     {
    #       "url" : "country",
    #       "valueCode" : "GB"
    #     },
    #     {
    #       "url" : "region",
    #       "valueCode" : "AU-NSW"
    #     },
    #     {
    #       "url" : "site",
    #       "valueIdentifier" : {
    #         "system" : "https://example.org/site-identifier",
    #         "value" : "sss"
    #       }
    #     },
    #     {
    #       "url" : "approvalDate",
    #       "valueDate" : "2017-12-05"
    #     },
    #     {
    #       "url" : "signature",
    #       "valueSignature" : {
    #         "data" : "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPEVudmVsb3BlIHhtbG5zPSJ1cm46ZW52ZWxvcGUiPgogIDxTaWduYXR1cmUgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvMDkveG1sZHNpZyMiPgogICAgPFNpZ25lZEluZm8+CiAgICAgIDxDYW5vbmljYWxpemF0aW9uTWV0aG9kIAogICAgICAgICAgIEFsZ29yaXRobT0iaHR0cDovL3d3dy53My5vcmcvVFIvMjAwMS9SRUMteG1sLWMxNG4tCjIwMDEwMzE1I1dpdGhDb21tZW50cyIvPgogICAgICA8U2lnbmF0dXJlTWV0aG9kIEFsZ29yaXRobT0iaHR0cDovL3d3dy53My5vcmcvMjAwMC8wOS8KeG1sZHNpZyNkc2Etc2hhMSIvPgogICAgICA8UmVmZXJlbmNlIFVSST0iIj4KICAgICAgICA8VHJhbnNmb3Jtcz4KICAgICAgICAgIDxUcmFuc2Zvcm0gQWxnb3JpdGhtPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwLzA5Lwp4bWxkc2lnI2VudmVsb3BlZC1zaWduYXR1cmUiLz4KICAgICAgICA8L1RyYW5zZm9ybXM+CiAgICAgICAgPERpZ2VzdE1ldGhvZCBBbGdvcml0aG09Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvMDkvCnhtbGRzaWcjc2hhMSIvPgogICAgICAgIDxEaWdlc3RWYWx1ZT51b29xYldZYTVWQ3FjSkNidXltQktxbTE3dlk9PC9EaWdlc3RWYWx1ZT4KICAgICAgPC9SZWZlcmVuY2U+CiAgICA8L1NpZ25lZEluZm8+CjxTaWduYXR1cmVWYWx1ZT4KS2VkSnVUb2I1Z3R2WXg5cU0zazNnbTdrYkxCd1ZiRVFSbDI2UzJ0bVhqcU5ORDdNUkd0b2V3PT0KICAgIDwvU2lnbmF0dXJlVmFsdWU+CiAgICA8S2V5SW5mbz4KICAgICAgPEtleVZhbHVlPgogICAgICAgIDxEU0FLZXlWYWx1ZT4KICAgICAgICAgIDxQPgovS2FDem80U3lyb203OHozRVE1U2JiQjRzRjdleTgwZXRLSUk4NjRXRjY0QjgxdVJwSDV0OWpRVHhlCkV1MEltYnpSTXF6VkRaa1ZHOXhEN25OMWt1Rnc9PQogICAgICAgICAgPC9QPgogICAgICAgICAgPFE+bGk3ZHpEYWN1bzY3Smc3bXRxRW0yVFJ1T01VPTwvUT4KICAgICAgICAgIDxHPlo0UnhzbnFjOUU3cEdrbkZGSDJ4cWFyeVJQQmFRMDFraHBNZExSUW5HNTQxQXd0eC8KWFBhRjVCcHN5NHBOV01PSENCaU5VME5vZ3BzUVc1UXZubE1wQT09CiAgICAgICAgICA8L0c+CiAgICAgICAgICA8WT5xVjM4SXFyV0pHMFYvCm1aUXZSVmkxT0h3OVpqODRuREM0ak84UDBheGkxZ2I2ZCs0NzV5aE1qU2MvCkJySVZDNThXM3lkYmtLK1JpNE9LYmFSWmxZZVJBPT0KICAgICAgICAgPC9ZPgogICAgICAgIDwvRFNBS2V5VmFsdWU+CiAgICAgIDwvS2V5VmFsdWU+CiAgICA8L0tleUluZm8+CiAgPC9TaWduYXR1cmU+CjwvRW52ZWxvcGU+IA=="
    #       }
    #     },
    #     {
    #       "url" : "signatureUrl",
    #       "valueUrl" : "https://somelocation"
    #     },
    #     {
    #       "url" : "signatureMethod",
    #       "valueString" : "electronic and wet ink copy"
    #     },
    #     {
    #       "extension" : [
    #         {
    #           "url" : "scope",
    #           "valueCode" : "C41065"
    #         },
    #         {
    #           "url" : "number",
    #           "valuePositiveInt" : 234
    #         }
    #       ],
    #       "url" : "http://hl7.org/fhir/uv/clinical-study-protocol/StructureDefinition/ResearchStudyStudyAmendmentScopeImpact"
    #     },
    #     {
    #       "extension" : [
    #         {
    #           "url" : "scope",
    #           "valueCode" : "C68846"
    #         },
    #         {
    #           "url" : "number",
    #           "valuePositiveInt" : 983
    #         }
    #       ],
    #       "url" : "http://hl7.org/fhir/uv/clinical-study-protocol/StructureDefinition/ResearchStudyStudyAmendmentScopeImpact"
    #     },
