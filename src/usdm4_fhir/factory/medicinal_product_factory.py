from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.medicinalproductdefinition import MedicinalProductDefinition


class MedicinalProductDefinitionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = MedicinalProductDefinition(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)