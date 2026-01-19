from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.activitydefinition import ActivityDefinition


class ActivityDefinitionFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.activity_definition_factory.ActivityDefinitionFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            self.item = ActivityDefinition(**kwargs)
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
