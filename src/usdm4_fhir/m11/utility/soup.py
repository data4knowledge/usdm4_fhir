import warnings
from bs4 import BeautifulSoup
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


def get_soup(text: str, errors: Errors) -> BeautifulSoup:
    MODULE = "usdm4_fhir.m11.soup.soup"
    try:
        with warnings.catch_warnings(record=True) as warning_list:
            result = BeautifulSoup(text, "html.parser")
        if warning_list:
            for item in warning_list:
                errors.debug(
                    f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'",
                    KlassMethodLocation(MODULE, "get_soup"),
                )
        return result
    except Exception as e:
        errors.exception(
            f"Parsing '{text}' with soup", e, KlassMethodLocation(MODULE, "get_soup")
        )
        return BeautifulSoup("", "html.parser")
