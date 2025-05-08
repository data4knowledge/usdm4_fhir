from usdm3.data_store.data_store import DataStore
from src.usdm_fhir.errors.errors import Errors, Location
from usdm_fhir.m11.utility.soup import get_soup


class TagReference:
    MODULE = "src.usdm_fhir.m11.reference_resolver.ReferenceResolver"

    def __init__(self, data_store: DataStore):
        self._data_store = data_store
        self.errors = Errors()

    def translate(self, text: str):
        soup = get_soup(text)
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
        dictionary = self._data_store.instance_by_id(instance.dictionaryId)
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
                            f"Missing dictionary entry while attempting to resolve reference '{attributes}' while generating the FHIR message",
                            Location(self.MODULE, "_resolve_instance"),
                        )
                        self._replace_and_highlight(
                            ref, "Missing content: missing dictionary entry"
                        )
                else:
                    self.errors.error(
                        f"Missing dictionary while attempting to resolve reference '{attributes}' while generating the FHIR message",
                        Location(self.MODULE, "_resolve_instance"),
                    )
                    self._replace_and_highlight(
                        ref, "Missing content: missing dictionary"
                    )
            except Exception as e:
                self.errors.exception(
                    f"Failed to resolve reference '{attributes} while generating the FHIR message",
                    Location(self.MODULE, "_resolve_instance"),
                    e,
                )
                self._replace_and_highlight(ref, "Missing content: exception")
        return str(soup)

    def _replace_and_highlight(self, ref, text):
        ref.replace_with(text)
