import warnings
from bs4 import BeautifulSoup
from src.usdm_fhir.errors.errors import Errors, Location


def get_soup(text: str, errors: Errors):
    LOCATION = "src.usdm_fhir.m11.soup.soup"
    try:
        with warnings.catch_warnings(record=True) as warning_list:
            result = BeautifulSoup(text, "html.parser")
        if warning_list:
            for item in warning_list:
                errors.debug(
                    f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'",
                    Location(LOCATION, "get_soup"),
                )
        return result
    except Exception as e:
        errors.exception(
            f"Parsing '{text}' with soup", Location(LOCATION, "get_soup"), e
        )
        return ""
