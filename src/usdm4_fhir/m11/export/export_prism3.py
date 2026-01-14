from uuid import uuid4
from usdm4_fhir.m11.export.export_base import ExportBase
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.narrative_content import NarrativeContent
from usdm4.api.eligibility_criterion import EligibilityCriterion
from usdm4_fhir.factory.research_study_factory_p3 import ResearchStudyFactoryP3
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.reference_factory import ReferenceFactory
from usdm4_fhir.factory.composition_factory import CompositionFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory
from fhir.resources.bundle import Bundle, BundleEntry
from usdm4_fhir.factory.group_factory import GroupFactory
from usdm4_fhir.factory.coding_factory import CodingFactory


class ExportPRISM3(ExportBase):
    MODULE = "usdm4_fhir.m11.export.export_prism3.ExportPRISM3"
    IGNORE_LIST = ["", "5.2", "5.3"]

    class LogicError(Exception):
        pass

    def to_message(self) -> str | None:
        try:
            ie = self._create_ie_critieria()
            compositions = self._create_compositions()
            #compositions = []
            rs: ResearchStudyFactoryP3 = self._research_study(compositions, ie)
            bundle: Bundle = self._bundle(rs, compositions, ie)
            return bundle.json()
        except Exception as e:
            self._errors.exception(
                "Exception raised generating FHIR content.",
                e,
                KlassMethodLocation(self.MODULE, "export"),
            )
            return None

    def _bundle(
        self,
        research_study: ResearchStudyFactoryP3,
        compositions: list[CompositionFactory],
        ie: GroupFactory
    ):
        entries = []

        # Compositions
        composition: CompositionFactory
        for composition in compositions:
            entry = BundleEntry(
                resource=composition.item,
                request={"method": "PUT", "url": f"Composition/{composition.item.id}"},
            )
            entries.append(entry)
        for resource in research_study.resources:
            klass = resource.item.__class__.__name__
            entry = BundleEntry(
                resource=resource.item,
                request={"method": "PUT", "url": f"{klass}/{resource.item.id}"},
            )
            entries.append(entry)

        # IE Group
        entry = BundleEntry(
            resource=ie.item,
            request={"method": "PUT", "url": f"Group/{ie.item.id}"},
        )
        entries.append(entry)

        # RS
        entry = BundleEntry(
            resource=research_study.item,
            request={"method": "PUT", "url": f"ResearchStudy/{research_study.item.id}"},
        )
        entries.append(entry)

        # Overall bundle
        bundle = Bundle(
            id=None,
            entry=entries,
            type="transaction",
            # identifier=identifier,
            # timestamp=date_str,
        )
        return bundle

    def _research_study(
        self, compositions: list[CompositionFactory], ie: GroupFactory
    ) -> ResearchStudyFactoryP3:
        rs: ResearchStudyFactoryP3 = ResearchStudyFactoryP3(self.study, self._extra)
        composition: CompositionFactory
        for composition in compositions:
            ext: ExtensionFactory = ExtensionFactory(
                **{
                    "url": "http://hl7.org/fhir/uv/pharmaceutical-research-protocol/StructureDefinition/narrative-elements",
                    "valueReference": {
                        "reference": f"Composition/{composition.item.id}"
                    },
                }
            )
            rs.item.extension.append(ext.item)
        rs.item.recruitment = {"eligibility": {"reference": f"Group/{ie.item.id}"}}    
        return rs

    def _create_compositions(self):
        processed_map = {}
        compositions = []
        contents = self.protocol_document_version.narrative_content_in_order()
        content: NarrativeContent
        for content in contents:
            composition = self._content_to_composition_entry(content, processed_map)
            if composition:
                composition.item.id = str(uuid4())
                compositions.append(composition)
        return compositions

    def _content_to_composition_entry(
        self, content: NarrativeContent, processed_map: dict
    ):
        section = self._content_to_section(content, processed_map, self.IGNORE_LIST)
        if section:
            code = CodingFactory(
                system="http://hl7.org/fhir/research-study-party-role",
                code="b001",
                display="Protocol narative",
            )
            type_code = CodeableConceptFactory(coding=[code.item])
            author = ReferenceFactory(display="USDM").item
            return CompositionFactory(
                title=section.title,
                date=self._now,
                type=type_code.item,
                section=[section],
                status="preliminary",
                author=[author],
            )
        else:
            return None

    def _create_ie_critieria(self):
        design = self.study_design
        criteria = design.criterion_map()
        all_of: ExtensionFactory = ExtensionFactory(
            **{
                "url": "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.description",
                "valueString": "all-of",
            }
        )
        group = GroupFactory(
            id=str(uuid4()),
            characteristic=[],
            type="person",
            membership="definitional",
            extension=[all_of.item],
        )
        for _, id in enumerate(design.population.criterionIds):
            criterion = criteria[id]
            self._criterion(criterion, group.item.characteristic)
        return group

    def _criterion(self, criterion: EligibilityCriterion, collection: list):
        version = self.study_version
        na = CodeableConceptFactory(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                    "valueCode": "not-applicable",
                }
            ]
        )
        criterion_item = version.criterion_item(criterion.criterionItemId)
        if criterion_item:
            text = self.tag_ref.translate(criterion_item, criterion_item.text)
            if text:
                outer: ExtensionFactory = ExtensionFactory(
                    **{
                        "url": "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description",
                        "valueString": str(text),
                    }
                )
                if outer:
                    exclude = True if criterion.category.code == "C25370" else False
                    collection.append(
                        {
                            "extension": [outer.item],
                            "code": na.item,
                            "valueCodeableConcept": na.item,
                            "exclude": exclude,
                        }
                    )
                else:
                    self._errors.warning(
                        f"Criterion item with id '{criterion_item.id}' failed to create extension, text '{criterion_item.text}' -translated-> '{text}'"
                    )
            else:
                self._errors.warning(
                    f"Criterion item with id '{criterion_item.id}' has empty text, text '{criterion_item.text}' -translated-> '{text}'"
                )

    # First cut of amendment code. Example structure
    # ==============================================
    #
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
        # {
        #   "url" : "primaryReason",
        #   "valueCodeableConcept" : {
        #     "coding" : [
        #       {
        #         "system" : "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        #         "code" : "C218490",
        #         "display" : "Regulatory Agency Request To Amend"
        #       }
        #     ]
        #   }
        # },
        # {
        #   "url" : "secondaryReason",
        #   "valueCodeableConcept" : {
        #     "coding" : [
        #       {
        #         "system" : "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        #         "code" : "C218494",
        #         "display" : "Manufacturing Change"
        #       }
        #     ]
        #   }
        # },
        # {
        #   "url" : "summary",
        #   "valueString" : "Regulator required manufacturing chanage."
        # },
        # {
        #   "url" : "substantialImpactSafety",
        #   "valueCode" : "C49488"
        # },
        # {
        #   "url" : "substantialImpactSafetyComment",
        #   "valueString" : "Specifically implemented to decrease safety risks."
        # },
        # {
        #   "url" : "substantialImpactReliability",
        #   "valueCode" : "C17998"
        # },
        # {
        #   "url" : "substantialImpactReliabilityComment",
        #   "valueString" : "ccc"
        # },
        # {
        #   "extension" : [
        #     {
        #       "url" : "detail",
        #       "valueString" : "amendment one"
        #     },
        #     {
        #       "url" : "rationale",
        #       "valueString" : "clarification"
        #     },
        #     {
        #       "url" : "section",
        #       "valueCodeableConcept" : {
        #         "coding" : [
        #           {
        #             "system" : "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        #             "code" : "C218515",
        #             "display" : "1.1 Protocol Synopsis"
        #           }
        #         ]
        #       }
        #     }
        #   ],
        #   "url" : "http://hl7.org/fhir/uv/clinical-study-protocol/StructureDefinition/protocol-amendment-detail"
        # },
    
    def _amendment_ext(self):
        if len(self.study_version.amendments) == 0:
            return None
        source = self.study_version.amendments[0]

    #     amendment: ExtensionFactory = ExtensionFactory(
    #         url="http://example.org/fhir/extension/studyAmendment", extension=[]
    #     )
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "amendmentNumber", valueString=self._title_page["amendment_identifier"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory("scope", valueString=self._title_page["amendment_scope"])
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "details", value=self._title_page["amendment_details"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "substantialImpactSafety", valueString=self._amendment["safety_impact"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "substantialImpactSafety", valueString=self._amendment["safety_impact_reason"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "substantialImpactSafety", valueBoolean=self._amendment["robustness_impact"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "substantialImpactSafety", valueString=self._amendment["robustness_impact_reason"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     primary = self._codeable_concept(
    #         self._coding_from_code(source.primaryReason.code)
    #     )
    #     ext: ExtensionFactory = ExtensionFactory(
    #         "http://hl7.org/fhir/uv/ebm/StructureDefinition/primaryReason",
    #         value=primary,
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #         secondary = self._codeable_concept(
    #             self._coding_from_code(source.secondaryReasons[0].code)
    #         )
    #         ext = self._extension_codeable(
    #             "http://hl7.org/fhir/uv/ebm/StructureDefinition/secondaryReason",
    #             value=secondary,
    #         )
    #         if ext:
    #             amendment.extension.append(ext)
    #     return amendment
