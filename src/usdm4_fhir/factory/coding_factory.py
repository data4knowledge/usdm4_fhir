from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.coding import Coding


class CodingFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.coding_factory.CodingFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            if "usdm_code" in kwargs:
                kwargs["system"] = kwargs["usdm_code"].codeSystem
                kwargs["version"] = kwargs["usdm_code"].codeSystemVersion
                kwargs["code"] = kwargs["usdm_code"].code
                kwargs["display"] = kwargs["usdm_code"].decode
                kwargs.pop("usdm_code")
            self.item = Coding(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
