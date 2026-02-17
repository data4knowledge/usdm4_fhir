from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.human_name_factory import HumanNameFactory
from fhir.resources.practitioner import Practitioner
from usdm4.api.assigned_person import AssignedPerson
from uuid import uuid4


class PractionerFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.organization_factory.PractitionerFactory"

    def __init__(self, errors: Errors, person: AssignedPerson):
        try:
            super().__init__(errors, **{})
            human_name = HumanNameFactory(errors, text=person.name)
            self.item = Practitioner(id=str(uuid4()), name=[human_name.item])
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
