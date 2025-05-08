from src.usdm_fhir.factory.base_factory import BaseFactory
from fhir.resources.reference import Reference


class ReferenceFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = Reference(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
