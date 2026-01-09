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


class ExportPRISM3(ExportBase):
    MODULE = "usdm4_fhir.m11.export.ExportPRISM3"

    class LogicError(Exception):
        pass

    def to_message(self) -> str | None:
        try:
            ie = self._create_ie_critieria()
            compositions = self._create_compositions()
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
        section = self._content_to_section(content, processed_map)
        if section:
            type_code = CodeableConceptFactory(text="EvidenceReport").item
            author = ReferenceFactory(display="USDM").item
            return CompositionFactory(
                title=section.title,
                date=self._now,
                type=type_code,
                section=[section],
                status="preliminary",
                author=[author],
            )
        else:
            return None

    def _create_ie_critieria(self):
        design = self.study_design
        criteria = design.criterion_map()
        # all_of = self._extension_string(
        #     "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.combinationMethod",
        #     "all-of",
        # )
        all_of: ExtensionFactory = ExtensionFactory(
            **{
                "url": "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description",
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
            # outer = self._extension_string(
            #     "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description",
            #     str(text),
            # )
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
                    f"Criterion item with id '{criterion_item.id}' caused an error, text '{criterion_item.text}' -translated-> '{text}'"
                )
