import json
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm_fhir.soa.export import Export

class USDMFHIR:
    def to_m11(self, usdm_filepath: str):
        pass

    def to_soa(self, usdm_filepath: str):
        study = self._usdm_study(usdm_filepath)
        ex = Export(study)
        return ex.to_message


    def _usdm_study(usdm_filepath: str) -> Study:
        with open(usdm_filepath) as f:
            data = json.load(f)
        usdm = USDM4()
        wrapper: Wrapper = usdm.from_json(data)
        return wrapper.study