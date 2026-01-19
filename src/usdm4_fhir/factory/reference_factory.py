from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.reference import Reference


class ReferenceFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.reference_factory.ReferenceFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = Reference(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
