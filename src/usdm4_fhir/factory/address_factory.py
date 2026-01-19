from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4.api.address import Address as USDMAddress
from fhir.resources.fhirtypes import AddressType


class AddressFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.address_factory.AddressFactory"

    def __init__(self, errors: Errors, address: USDMAddress):
        try:
            super().__init__(errors, **{})
            address_dict = dict(address)
            address_dict.pop("instanceType")
            result = {}
            for k, v in address_dict.items():
                if v:
                    result[k] = v
            if "lines" in result:
                result["line"] = result["lines"]
                result.pop("lines")
            if "country" in result:
                result["country"] = address.country.decode
            self.item = AddressType(**result)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
