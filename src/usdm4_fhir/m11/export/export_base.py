from usdm4.api.study import Study
from usdm4.api.narrative_content import NarrativeContent
from usdm4.api.study_version import StudyVersion
from usdm4_fhir.utility.data_store import DataStore
from usdm4_fhir.m11.utility.tag_reference import TagReference

from fhir.resources.composition import CompositionSection
from fhir.resources.narrative import Narrative
from fhir.resources.codeableconcept import CodeableConcept
from usdm4_fhir.m11.utility.soup import get_soup
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


class ExportBase:
    EMPTY_DIV = '<div xmlns="http://www.w3.org/1999/xhtml"></div>'
    MODULE = "usdm4_fhir.m11.export.export_base.ExportBase"

    class LogicError(Exception):
        pass

    def __init__(self, study: Study, extra: dict):
        self.study = study
        self._uuid = study.id
        self._data_store = DataStore(study)
        self._extra = extra
        self._title_page = extra["title_page"]
        self._miscellaneous = extra["miscellaneous"]
        self._amendment = extra["amendment"]
        self._errors = Errors()
        self.study_version: StudyVersion = study.first_version()
        self.study_design = self.study_version.studyDesigns[0]
        self.protocol_document_version = self.study.documentedBy[0].versions[0]
        self.tag_ref = TagReference(self._data_store, self._errors)
        self._nc_map = self.protocol_document_version.narraitve_content_map()
        self._nci_map = self.study_version.narrative_content_item_map()

    @property
    def errors(self) -> Errors:
        return self._errors

    def _process_sections(self) -> list:
        sections = []
        processed_map = {}
        content = self.protocol_document_version.contents[0]
        more = True
        while more:
            section = self._content_to_section(content, processed_map)
            if section:
                sections.append(section)
            content = self._next_narrative_content(content, processed_map)
            more = True if content else False
        return sections

    def _next_narrative_content(
        self, content: NarrativeContent, map: dict
    ) -> NarrativeContent | None:
        processed = True
        while processed:
            if content.nextId:
                content: NarrativeContent = self._nc_map[content.nextId]
                if content.id not in map:
                    return content
            else:
                processed = False
        return None

    def _content_to_section(
        self, content: NarrativeContent, processed_map: dict
    ) -> CompositionSection:
        # print(f"CONTENT TO SECTION: {content}")
        processed_map[content.id] = True
        content_text = self._narrative_content_item(content)
        div = self.tag_ref.translate(content_text)
        text = str(div)
        text = self._remove_line_feeds(text)
        narrative = Narrative(status="generated", div=text)
        title = self._format_section_title(content.sectionTitle)
        code = CodeableConcept(text=f"section{content.sectionNumber}-{title}")
        title = content.sectionTitle if content.sectionTitle else ""
        section = self._composition_section(f"{title}", code, narrative)
        if self._composition_section_no_text(section) and not content.childIds:
            return None
        else:
            for id in content.childIds:
                content = self._nc_map[id]
                child = self._content_to_section(content, processed_map)
                if child:
                    section.section.append(child)
        return section

    def _narrative_content_item(self, content: NarrativeContent) -> str:
        nci = self._nci_map[content.contentItemId]
        return nci.text if nci else ""

    def _format_section_title(self, title: str) -> str:
        return title.lower().strip().replace(" ", "-")

    def _clean_section_number(self, section_number: str) -> str:
        return section_number[:-1] if section_number.endswith(".") else section_number

    def _remove_line_feeds(self, div: str) -> str:
        text = div.replace("\n", "")
        return text

    # Factory
    def _composition_section_no_text(self, section):
        return section.text is None

    # Factory
    def _composition_section(self, title, code, narrative: Narrative):
        if narrative.div == "&amp;nbsp":
            narrative.div = self.EMPTY_DIV
        narrative.div = self._clean_tags(narrative.div)
        if narrative.div == self.EMPTY_DIV:
            return CompositionSection(title=f"{title}", code=code, section=[])
        else:
            return CompositionSection(
                title=f"{title}", code=code, text=narrative, section=[]
            )

    def _clean_tags(self, content):
        soup = get_soup(content, self._errors)
        # 'ol' tag with 'type' attribute
        for ref in soup("ol"):
            try:
                attributes = ref.attrs
                if "type" in attributes:
                    ref.attrs = {}
            except Exception as e:
                location = KlassMethodLocation(self.MODULE, "_clean_tag")
                self._errors.exception(
                    "Exception raised cleaning 'ol' tags", e, location
                )
        # Styles
        for ref in soup("style"):
            try:
                ref.extract()
            except Exception as e:
                location = KlassMethodLocation(self.MODULE, "_clean_tag")
                self._errors.exception(
                    "Exception raised cleaning 'script' tags", e, location
                )
        # Images
        # for ref in soup('img'):
        #   try:
        #     ref.extract()
        #   except Exception as e:
        #     self._errors_and_logging.exception(f"Exception raised cleaning 'img' tags", e)
        # Empty 'p' tags
        for ref in soup("p"):
            try:
                if len(ref.get_text(strip=True)) == 0:
                    ref.extract()
            except Exception as e:
                location = KlassMethodLocation(
                    "usdm4_fhir.m11.export.export_base.ExportBase", "_clean_tag"
                )
                self._errors.exception(
                    "Exception raised cleaning empty 'p' tags", e, location
                )
        return str(soup)
