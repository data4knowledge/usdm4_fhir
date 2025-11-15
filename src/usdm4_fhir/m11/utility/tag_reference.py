from bs4 import BeautifulSoup
from usdm4_fhir.utility.data_store import DataStore
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.syntax_template_dictionary import SyntaxTemplateDictionary, ParameterMap
from usdm4_fhir.m11.utility.soup import get_soup


class TagReference:
    MODULE = "usdm4_fhir.m11.reference_resolver.ReferenceResolver"

    def __init__(self, data_store: DataStore, errors: Errors):
        self._data_store = data_store
        self._errors = errors

    def translate(self, instance: object, text: str) -> str:
        if text:
            soup = get_soup(text, self._errors)
            return str(self._translate_references(instance, soup))
        else:
            return ""

    def _translate_references(
        self, instance: object, soup: BeautifulSoup
    ) -> BeautifulSoup:
        ref: BeautifulSoup
        for ref in soup(["usdm:ref", "usdm:tag"]):
            try:
                if ref.name == "usdm:ref":
                    instance, text = self._resolve_usdm_ref(instance, ref)
                    ref.replace_with(self._translate_references(instance, text))
                if ref.name == "usdm:tag":
                    instance, text = self._resolve_usdm_tag(instance, ref)
                    ref.replace_with(self._translate_references(instance, text))
            except Exception as e:
                print(f"TEXT: {text}, {instance.model_dump()}")
                self._errors.exception(
                    f"Exception raised while attempting to translate '{ref}' in instance '{instance.id}'",
                    e,
                    KlassMethodLocation(self.MODULE, "_translate_references"),
                )
        return soup

    def _resolve_usdm_ref(
        self, instance: object, ref: BeautifulSoup
    ) -> tuple[object, BeautifulSoup]:
        attributes = ref.attrs
        instance = self._data_store.get(attributes["klass"], attributes["id"])
        value = str(getattr(instance, attributes["attribute"]))
        return instance, get_soup(value, self._errors)

    def _resolve_usdm_tag(
        self, instance: object, ref: BeautifulSoup
    ) -> tuple[object, BeautifulSoup]:
        attributes = ref.attrs
        dictionary: SyntaxTemplateDictionary = self._data_store.get(
            "SyntaxTemplateDictionary", instance.dictionaryId
        )
        if dictionary:
            p_map: ParameterMap
            for p_map in dictionary.parameterMaps:
                if p_map.tag == attributes["name"]:
                    return instance, get_soup(p_map.reference, self._errors)
        error_text = (
            f"tag '{attributes['name']}' not found"
            if dictionary
            else "no dictionary found"
        )
        self._errors.error(
            f"Error translating tag '{ref}' in instance '{instance.id}, {error_text}",
            KlassMethodLocation(self.MODULE, "_resolve_usdm_tag"),
        )
        return instance, get_soup(f"<i>{error_text}</i>", self._errors)
