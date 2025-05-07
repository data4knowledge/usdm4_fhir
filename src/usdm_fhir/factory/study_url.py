from usdm4.api.study import Study
from src.usdm_fhir.factory.base_factory import BaseFactory


class StudyUrl:
    @classmethod
    def generate(cls, study: Study) -> str:
        return f"http://d4k.dk/fhir/vulcan-soa/{BaseFactory.fix_id(study.name)}"
