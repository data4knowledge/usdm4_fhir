from uuid import uuid4
from usdm4.api.study import Study
from usdm4.api.narrative_content import NarrativeContent
from usdm4.api.study_title import StudyTitle as USDMStudyTitle
from usdm3.data_store.data_store import DataStore
from usdm4.api.study_version import StudyVersion

from usdm_fhir.m11.tag_reference import TagReference

from fhir.resources.composition import CompositionSection
from fhir.resources.narrative import Narrative
from fhir.resources.codeableconcept import CodeableConcept
from src.usdm_fhir.m11.soup import get_soup


class ExportBase:
    EMPTY_DIV = '<div xmlns="http://www.w3.org/1999/xhtml"></div>'

    class LogicError(Exception):
        pass

    def __init__(self, study: Study, data_store: DataStore, extra: dict = {}):
        self.study = study
        self._data_store = data_store
        # self._uuid = uuid
        self._title_page = extra["title_page"]
        self._miscellaneous = extra["miscellaneous"]
        self._amendment = extra["amendment"]
        # self._errors_and_logging = ErrorsAndLogging()
        # self._cross_ref = CrossReference(study, self._errors_and_logging)
        self.study_version: StudyVersion = study.first_version()
        self._nci_map = self.study_version.narrative_content_item_map()
        self.study_design = self.study_version.studyDesigns[0]
        self.protocol_document_version = self.study.documentedBy[0].versions[0]
        self.doc_title = self.study_version.official_title()
        self.tag_ref = TagReference(self._data_store)

    def _content_to_section(self, content: NarrativeContent) -> CompositionSection:
        content_text = self._section_item(content)
        div = self.tag_ref.translate(content_text)
        text = str(div)
        text = self._remove_line_feeds(text)
        narrative = Narrative(status="generated", div=text)
        title = self._format_section_title(content.sectionTitle)
        code = CodeableConcept(text=f"section{content.sectionNumber}-{title}")
        title = content.sectionTitle if content.sectionTitle else "&nbsp;"
        section = self._composition_section(f"{title}", code, narrative)
        if self._composition_section_no_text(section) and not content.childIds:
            return None
        else:
            for id in content.childIds:
                content = self.protocol_document_version.find_narrative_content(id)
                child = self._content_to_section(content)
                if child:
                    section.section.append(child)
            return section

    def _section_item(self, content: NarrativeContent) -> str:
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
    def _composition_section(self, title, code, narrative):
        # print(f"NARRATIVE: {narrative.div[0:50]}")
        narrative.div = self._clean_tags(narrative.div)
        if narrative.div == self.EMPTY_DIV:
            # print("EMPTY")
            return CompositionSection(title=f"{title}", code=code, section=[])
        else:
            return CompositionSection(
                title=f"{title}", code=code, text=narrative, section=[]
            )

    def _clean_tags(self, content):
        soup = get_soup(content, self._errors_and_logging)
        # 'ol' tag with 'type' attribute
        for ref in soup("ol"):
            try:
                attributes = ref.attrs
                if "type" in attributes:
                    ref.attrs = {}
            except Exception as e:
                self._errors_and_logging.exception(
                    "Exception raised cleaning 'ol' tags", e
                )
        # Styles
        for ref in soup("style"):
            try:
                ref.extract()
            except Exception as e:
                self._errors_and_logging.exception(
                    "Exception raised cleaning 'script' tags", e
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
                self._errors_and_logging.exception(
                    "Exception raised cleaning empty 'p' tags", e
                )
        return str(soup)
