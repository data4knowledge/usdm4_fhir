from uuid import uuid4
from usdm4_fhir.m11.export.export_base import ExportBase
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.narrative_content import NarrativeContent
from usdm4_fhir.factory.research_study_factory_p3 import ResearchStudyFactoryP3
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.reference_factory import ReferenceFactory
from usdm4_fhir.factory.composition_factory import CompositionFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory
from fhir.resources.bundle import Bundle, BundleEntry


class ExportPRISM3(ExportBase):
    MODULE = "usdm4_fhir.m11.export.ExportPRISM3"

    class LogicError(Exception):
        pass

    def to_message(self) -> str | None:
        try:
            # Compositions
            compositions = self._create_compositions()
            rs: ResearchStudyFactoryP3 = self._research_study(compositions)
            bundle: Bundle = self._bundle(rs, compositions)
            return bundle.json()
        except Exception as e:
            self._errors.exception(
                "Exception raised generating FHIR content.",
                e,
                KlassMethodLocation(self.MODULE, "export"),
            )
            return None

    def _bundle(self, research_study: ResearchStudyFactoryP3, compositions: list[CompositionFactory]):
        entries = []
        composition: CompositionFactory
        for composition in compositions:
            entry = BundleEntry(
                resource=composition.item, request={
                    "method": "PUT",
                    "url": f"Composition/{composition.item.id}"
                }
            )
            entries.append(entry)
        entry = BundleEntry(
            resource=research_study.item, request={
                "method": "PUT",
                "url": f"ResearchStudy/{research_study.item.id}"
            }
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

    def _research_study(self, compositions: list[CompositionFactory]) -> ResearchStudyFactoryP3:
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