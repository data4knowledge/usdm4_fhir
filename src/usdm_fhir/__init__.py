from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm_fhir.soa.export.export import Export as SoAExport
from usdm_fhir.m11.export.export import Export as M11Export
from usdm_fhir.utility.data_store import DataStore


class FHIRBase:
    def __init__(self):
        self._usdm = USDM4()
        self._data_store = None
        self.export = None


class M11(FHIRBase):
    def to_m11(self, study: Study, extra: dict):
        self.export = M11Export(study, extra)
        return self.export.to_message()

    def errors(self) -> dict:
        return self.export.errors.dump(self.export.errors.ERROR)


class SoA(FHIRBase):
    def to_message(self, study: Study, extra: dict):
        self.export = SoAExport(study, extra)
        return self.export.to_message()
