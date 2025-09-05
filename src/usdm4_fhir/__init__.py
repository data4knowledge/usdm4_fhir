from usdm4 import USDM4
from simple_error_log import Errors
from usdm4.api.study import Study
from usdm4_fhir.soa.export.export import Export as SoAExport
from usdm4_fhir.m11.export.export_madrid import ExportMadrid


class FHIRBase:
    def __init__(self):
        self._usdm = USDM4()
        self._data_store = None
        self._export = None


class M11(FHIRBase):
    def to_message(self, study: Study, extra: dict) -> str | None:
        self._export = ExportMadrid(study, extra)
        return self._export.to_message()

    @property
    def errors(self) -> Errors:
        return self._export.errors


class SoA(FHIRBase):
    def to_message(self, study: Study, extra: dict):
        self.export = SoAExport(study, extra)
        return self.export.to_message()
