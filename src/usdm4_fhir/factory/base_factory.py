import re
from simple_error_log import Errors
from simple_error_log.error_location import KlassMethodLocation

class BaseFactory:
    def __init__(self, errors: Errors, **kwargs):
        self._errors = errors
        self.item = None

    def handle_exception(self, module: str, method: str, e: Exception):
        self.item = None
        self._errors.exception("Exception rasied in factory method.", e, KlassMethodLocation(module, method))

    @staticmethod
    def fix_id(value: str) -> str:
        result = re.sub("[^0-9a-zA-Z]", "-", value)
        result = "-".join([s for s in result.split("-") if s != ""])
        return result.lower()
