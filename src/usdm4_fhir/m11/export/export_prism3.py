import datetime
from uuid import uuid4
from usdm4.api.eligibility_criterion import EligibilityCriterion
from usdm4_fhir.m11.export.export_base import ExportBase
from usdm4_fhir.m11.utility.soup import get_soup
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.research_study_factory_p3 import ResearchStudyFactoryP3
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.reference_factory import ReferenceFactory
from usdm4_fhir.factory.composition_factory import CompositionFactory
from usdm4_fhir.factory.bundle_entry_factory import BundleEntryFactory
from usdm4_fhir.factory.bundle_factory import BundleFactory
from usdm4_fhir.factory.identifier_factory import IdentifierFactory
from usdm4_fhir.factory.extension_factory import ExtensionFactory
from usdm4_fhir.factory.group_factory import GroupFactory


class ExportPRISM3(ExportBase):
    MODULE = "usdm4_fhir.m11.export.ExportPRISM3"

    class LogicError(Exception):
        pass

    def to_message(self) -> str | None:
        try:
            # Compositions
            compositions = self._create_compositions()

            # Research Study
            rs: ResearchStudyFactoryP3 = ResearchStudyFactoryP3(self.study, self._extra)
            rs.item.extension.append(compositions)
            return rs.item.json()
        except Exception as e:
            self._errors.exception(
                "Exception raised generating FHIR content.",
                e,
                KlassMethodLocation(self.MODULE, "export"),
            )
            return None

    def _create_compositions(self):
        processed_map = {}
        compositions = []
        contents = self.protocol_document_version.narrative_content_in_order()
        content: NarrativeContent
        for content in contents:
            section = self._content_to_composition_entry(content, processed_map)
            if section:
                compositions.append(section.item)
        return compositions

    def _content_to_composition_entry(self, content: NarrativeContent, processed_map: dict):
        section = self._content_to_section(content, processed_map)
        type_code = CodeableConceptFactory(text="EvidenceReport").item
        author = ReferenceFactory(display="USDM").item
        return CompositionFactory(
            title="ccc",
            date="2025-06-30T12:46:00Z",
            type=type_code,
            section=[section],
            status="preliminary",
            author=[author],
        )

