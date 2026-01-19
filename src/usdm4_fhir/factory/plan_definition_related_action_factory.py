from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.plandefinition import PlanDefinitionActionRelatedAction


class PlanDefinitionRelatedActionFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.plan_definition_related_action_factory.PlanDefinitionRelatedActionFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = PlanDefinitionActionRelatedAction(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
