import json
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm_fhir.soa.export.export import Export as SoAExport
from usdm_fhir.m11.export.export import Export as M11Export
from usdm3.data_store.data_store import DataStore


class USDMFHIR:
    def __init__(self):
        self._usdm = USDM4()
        self._data_store = None

    def to_m11(self, usdm_filepath: str, extra: dict):
        study = self._usdm_study(usdm_filepath)
        ex = M11Export(study, self._data_store, extra)
        return ex.to_message()

    def to_soa(self, usdm_filepath: str, extra: dict):
        study = self._usdm_study(usdm_filepath)
        ex = SoAExport(study, extra)
        return ex.to_message()

    def _usdm_study(self, usdm_filepath: str) -> Study:
        self.data_store = DataStore(usdm_filepath)
        self.data_store.decompose()
        #print(f"DATA: {self.data_store.data}")
        wrapper: Wrapper = self._usdm.from_json(self.data_store.data)
        return wrapper.study
