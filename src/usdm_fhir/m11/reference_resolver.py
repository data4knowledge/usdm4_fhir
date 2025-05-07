import warnings
from bs4 import BeautifulSoup
from usdm3.data_store.data_store import DataStore
from src.usdm_fhir.errors.errors import Errors, Location

class ReferenceResolver:
    MODULE = "src.usdm_fhir.m11.reference_resoolver.ReferenceResolver"

    def __init__(self, data_store: DataStore):
        self._data_store = data_store
        self.errors = Errors()

    def translate(self, text: str):
        soup = self._get_soup(text)
        for ref in soup(["usdm:ref"]):
            try:
                attributes = ref.attrs
                instance = self._data_store.instance_by_id(attributes["id"])
                value = self._resolve_instance(instance, attributes["attribute"])
                translated_text = self.translate(value)
                self._replace_and_highlight(ref, translated_text)
            except Exception as e:
                location = Location(self.MODULE, "translate")
                self.errors.exception(
                    f"Exception raised while attempting to translate reference '{attributes}' while generating the FHIR message, see the logs for more info",
                    location,
                    e,
                )
                self._replace_and_highlight(ref, "Missing content: exception")
        return self._get_soup(str(soup))

    def _resolve_instance(self, instance, attribute):
        dictionary = self._get_dictionary(instance)
        value = str(getattr(instance, attribute))
        soup = self._get_soup(value, self._errors_and_logging)
        for ref in soup(["usdm:tag"]):
            try:
                attributes = ref.attrs
                if dictionary:
                    entry = next(
                        (
                            item
                            for item in dictionary.parameterMaps
                            if item.tag == attributes["name"]
                        ),
                        None,
                    )
                    if entry:
                        self._replace_and_highlight(
                            ref, get_soup(entry.reference, self._errors_and_logging)
                        )
                    else:
                        self._errors_and_logging.error(
                            f"Missing dictionary entry while attempting to resolve reference '{attributes}' while generating the FHIR message"
                        )
                        self._replace_and_highlight(
                            ref, "Missing content: missing dictionary entry"
                        )
                else:
                    self._errors_and_logging.error(
                        f"Missing dictionary while attempting to resolve reference '{attributes}' while generating the FHIR message"
                    )
                    self._replace_and_highlight(
                        ref, "Missing content: missing dictionary"
                    )
            except Exception as e:
                self._errors_and_logging.exception(
                    f"Failed to resolve reference '{attributes} while generating the FHIR message",
                    e,
                )
                self._replace_and_highlight(ref, "Missing content: exception")
        return str(soup)

    def _replace_and_highlight(self, ref, text):
        ref.replace_with(text)

    # # USDM4
    # def _get_dictionary(self, instance):
    #     try:
    #         return self._cross_ref.get(
    #             "SyntaxTemplateDictionary", instance.dictionaryId
    #         )
    #     except:
    #         return None

    # # def _add_section_heading(self, content: NarrativeContent, div) -> str:
    # #     DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
    # #     text = str(div)
    # #     text = text.replace(
    # #         DIV_OPEN_NS,
    # #         f"{DIV_OPEN_NS}<p>{content.sectionNumber} {content.sectionTitle}</p>",
    # #     )
    # #     return text

    # def _remove_line_feeds(self, div: str) -> str:
    #     text = div.replace("\n", "")
    #     return text

    # # USDM4
    # def _get_official_title(self) -> USDMStudyTitle:
    #     title = self._get_title("Official Study Title")
    #     return title.text if title else ""

    # # USDM4
    # def _get_title(self, title_type) -> USDMStudyTitle:
    #     for title in self.study_version.titles:
    #         if title.type.decode == title_type:
    #             return title
    #     return None


    # def _composition_section_no_text(self, section):
    #     return section.text is None

    # # Factory
    # def _composition_section(self, title, code, narrative):
    #     # print(f"NARRATIVE: {narrative.div[0:50]}")
    #     narrative.div = self._clean_tags(narrative.div)
    #     if narrative.div == self.EMPTY_DIV:
    #         # print("EMPTY")
    #         return CompositionSection(title=f"{title}", code=code, section=[])
    #     else:
    #         return CompositionSection(
    #             title=f"{title}", code=code, text=narrative, section=[]
    #         )

    # def _clean_tags(self, content):
    #     # print(f"Cleaning")
    #     before = content
    #     soup = get_soup(content, self._errors_and_logging)
    #     # 'ol' tag with 'type' attribute
    #     for ref in soup("ol"):
    #         try:
    #             attributes = ref.attrs
    #             if "type" in attributes:
    #                 ref.attrs = {}
    #         except Exception as e:
    #             self._errors_and_logging.exception(
    #                 "Exception raised cleaning 'ol' tags", e
    #             )
    #     # Styles
    #     for ref in soup("style"):
    #         try:
    #             ref.extract()
    #         except Exception as e:
    #             self._errors_and_logging.exception(
    #                 "Exception raised cleaning 'script' tags", e
    #             )
    #     # Images
    #     # for ref in soup('img'):
    #     #   try:
    #     #     ref.extract()
    #     #   except Exception as e:
    #     #     self._errors_and_logging.exception(f"Exception raised cleaning 'img' tags", e)
    #     # Empty 'p' tags
    #     for ref in soup("p"):
    #         try:
    #             if len(ref.get_text(strip=True)) == 0:
    #                 ref.extract()
    #         except Exception as e:
    #             self._errors_and_logging.exception(
    #                 "Exception raised cleaning empty 'p' tags", e
    #             )
    #     after = str(soup)
    #     # if before != after:
    #     #   print(f"Cleaning modified")
    #     return after


    def _get_soup(self, text: str):
        try:
            with warnings.catch_warnings(record=True) as warning_list:
                result = BeautifulSoup(text, "html.parser")
            if warning_list:
                for item in warning_list:
                    self.errors.debug(
                        f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'"
                    )
            return result
        except Exception as e:
            self.errors.exception(f"Parsing '{text}' with soup", e)
            return ""
