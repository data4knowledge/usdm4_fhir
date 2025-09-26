import os
from usdm4_fhir.status.files import read_yaml, root
from simple_error_log import Errors


class Status:
    MODULE = "usdm4_m11.status.status.Status"

    def __init__(self):
        self._root = root()
        self._errors = Errors()

    def status(self, name: str) -> dict:
        filename = "data/status/status.yaml"
        filepath = os.path.join(self._root, filename)
        elements = read_yaml(filepath)
        return elements[name]
