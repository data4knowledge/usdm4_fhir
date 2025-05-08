from src.usdm_fhir.factory.base_factory import BaseFactory
from fhir.resources.composition import Composition


class CompositionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = Composition(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
