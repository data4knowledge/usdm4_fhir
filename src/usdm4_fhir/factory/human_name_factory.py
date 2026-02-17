from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.humanname import HumanName


class HumanNameFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.codeable_concept_factory.HumanNameFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = HumanName(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
