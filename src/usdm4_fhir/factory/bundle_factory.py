from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.bundle import Bundle


class BundleFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.bundle_factory.BundleFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = Bundle(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
