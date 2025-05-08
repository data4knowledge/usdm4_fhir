import traceback
from d4k_sel.errors import Errors as BaseErrors
from d4k_sel.error_location import KlassMethodLocation as Location


class Errors(BaseErrors):
    def error(self, message: str, location: Location):
        self.add(message, location)

    def info(self, message: str, location: Location):
        self.add(message, location, level=BaseErrors.INFO)

    def debug(self, message: str, location: Location):
        self.add(message, location, level=BaseErrors.DEBUG)

    def exception(self, message: str, location: Location, e: Exception):
        message = f"{message}\n\nDetails\n{e}\n\nTraceback\n{traceback.format_exc()}"
        self.add(message, location)
