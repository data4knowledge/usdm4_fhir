from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.composition import Composition


class CompositionFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.composition_factory.CompositionFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = Composition(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
