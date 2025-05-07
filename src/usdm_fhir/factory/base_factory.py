import re


class BaseFactory:
    class FHIRError(Exception):
        pass

    def handle_exception(self, e: Exception):
        raise BaseFactory.FHIRError

    @staticmethod
    def fix_id(value: str) -> str:
        result = re.sub("[^0-9a-zA-Z]", "-", value)
        result = "-".join([s for s in result.split("-") if s != ""])
        return result.lower()
