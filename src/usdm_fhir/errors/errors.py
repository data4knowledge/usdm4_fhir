import traceback
from d4k_sel.errors import Errors as BaseErrors
from d4k_sel.error_location import KlassMethodLocation as Location

class Errors(BaseErrors):
    def exception(self, message: str, location: Location, e: Exception):
        message = f"message\n\nDetails\n{e}\n\nTraceback\n{traceback.format_exc()}"
        self.add(message, location)

