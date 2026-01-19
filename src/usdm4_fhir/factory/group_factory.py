from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.group import Group


class GroupFactory(BaseFactory):
    def __init__(self, errors: Errors, **kwargs):
        try:
            super.__init__(errors, **kwargs)
            self.item = Group(**kwargs)
        except Exception as e:
            self.handle_exception(e)
