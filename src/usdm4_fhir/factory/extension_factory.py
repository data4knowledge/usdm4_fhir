from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.extension import Extension


class ExtensionFactory(BaseFactory):
    def __init__(self, errors: Errors, **kwargs):
        try:
            super.__init__(errors, **kwargs)
            kwargs["extension"] = (
                [] if "extension" not in kwargs else kwargs["extension"]
            )
            self.item = Extension(**kwargs)
        except Exception as e:
            self.handle_exception(e)
