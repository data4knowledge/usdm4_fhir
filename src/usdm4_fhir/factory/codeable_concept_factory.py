from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.codeableconcept import CodeableConcept


class CodeableConceptFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.codeable_concept_factory.CodeableConceptFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = CodeableConcept(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
