from bs4 import BeautifulSoup
from usdm3.data_store.data_store import DataStore
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4_fhir.m11.utility.soup import get_soup


class TagReference:
    MODULE = "usdm4_fhir.m11.reference_resolver.ReferenceResolver"

    def __init__(self, data_store: DataStore, errors: Errors):
        self._data_store = data_store
        self.errors = errors

    def translate(self, text: str):
        soup = get_soup(text, self.errors)
        for ref in soup(["usdm:ref"]):
            try:
                attributes = ref.attrs
                instance = self._data_store.get(attributes["klass"], attributes["id"])
                value = self._resolve_instance(instance, attributes["attribute"])
                translated_text = self.translate(value)
                print(f"TRANSLATED: {translated_text}")
                self._replace_and_highlight(ref, translated_text)
            except Exception as e:
                location = KlassMethodLocation(self.MODULE, "translate")
                self.errors.exception(
                    f"Exception raised while attempting to translate reference '{attributes}'",
                    e,
                    location,
                )
                self._replace_and_highlight(ref, get_soup("Missing content: exception", self.errors))
        return get_soup(str(soup), self.errors)

    def _resolve_instance(self, instance, attribute):
        dictionary = self._get_dictionary(instance)
        value = str(getattr(instance, attribute))
        soup = get_soup(value, self.errors)
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
                            ref, get_soup(entry.reference, self.errors)
                        )
                    else:
                        self.errors.error(
                            f"Missing dictionary entry while attempting to resolve reference '{attributes}'",
                            KlassMethodLocation(self.MODULE, "_resolve_instance"),
                        )
                        self._replace_and_highlight(
                            ref, get_soup("Missing content: missing dictionary entry", self.errors)
                        )
                else:
                    self.errors.error(
                        f"Missing dictionary while attempting to resolve reference '{attributes}'",
                        KlassMethodLocation(self.MODULE, "_resolve_instance"),
                    )
                    self._replace_and_highlight(
                        ref, get_soup("Missing content: missing dictionary", self.errors)
                    )
            except Exception as e:
                self.errors.exception(
                    f"Failed to resolve reference '{attributes} while generating the FHIR message",
                    e,
                    KlassMethodLocation(self.MODULE, "_resolve_instance")
                )
                self._replace_and_highlight(ref, get_soup("Missing content: exception", self.errors))
        return str(soup)

    def _replace_and_highlight(self, ref, text: BeautifulSoup) -> None:
        ref.replace_with(text)

    def _get_dictionary(self, instance):
        try:
            return self._data_store.get(
                "SyntaxTemplateDictionary", instance.dictionaryId
            )
        except:
            return None
