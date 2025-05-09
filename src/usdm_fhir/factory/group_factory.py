from usdm_fhir.factory.base_factory import BaseFactory
from fhir.resources.group import Group


class GroupFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = Group(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
