from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.identifier import Identifier


class IdentifierFactory(BaseFactory):
    def __init__(self, errors: Errors, **kwargs):
        try:
            super.__init__(errors, **kwargs)
            self.item = Identifier(**kwargs)
        except Exception as e:
            self.handle_exception(e)
