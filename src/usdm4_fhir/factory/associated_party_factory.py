from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.researchstudy import ResearchStudyAssociatedParty
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory


class AssociatedPartyFactory(BaseFactory):
    MODULE = "usdm4_fhir.factory.associated_party_factory.AssociatedPartyFactory"

    def __init__(self, errors: Errors, **kwargs):
        try:
            super().__init__(errors, **kwargs)
            code = CodingFactory(
                errors=self._errors,
                system="http://hl7.org/fhir/research-study-party-role",
                code=kwargs["role_code"],
                display=kwargs["role_display"],
            )
            role = CodeableConceptFactory(errors=self._errors, coding=[code.item])
            self.item = ResearchStudyAssociatedParty(
                role=role.item, party=kwargs["party"]
            )
        except Exception as e:
            self.handle_exception(self.MODULE, "__init__", e)
