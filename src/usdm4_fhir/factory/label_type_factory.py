from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from fhir.resources.fhirtypes import ResearchStudyLabelType
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory


class LabelTypeFactory(BaseFactory):
    def __init__(self, errors: Errors, **kwargs):
        try:
            super.__init__(errors, **kwargs)
            coding = CodingFactory(usdm_code=kwargs["usdm_code"])
            type = CodeableConceptFactory(coding=[coding.item])
            self.item = ResearchStudyLabelType(type=type.item, value=kwargs["text"])
        except Exception as e:
            self.handle_exception(e)
