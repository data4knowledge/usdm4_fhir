from usdm4 import USDM4
from simple_error_log import Errors
from usdm4.api.study import Study
from usdm4_fhir.soa.export.export_soa import ExportSoA
from usdm4_fhir.m11.export.export_madrid import ExportMadrid
from usdm4_fhir.m11.export.export_prism2 import ExportPRISM2


class FHIRBase:
    def __init__(self):
        self._usdm = USDM4()
        self._export = None


class M11(FHIRBase):
    MADRID = "madrid"
    PRISM2 = "prism2"

    def to_message(self, study: Study, extra: dict, version: str = PRISM2) -> str | None:
        match version:
            case self.MADRID:
                self._export = ExportMadrid(study, extra)
            case self.PRISM2:
                self._export = ExportPRISM2(study, extra)
            case _:
                raise Exception(f"Version parameter '{version}' not recognized")
        return self._export.to_message()

    @property
    def errors(self) -> Errors:
        return self._export.errors


class SoA(FHIRBase):
    def to_message(self, study: Study, extra: dict) -> str | None:
        self._export = ExportSoA(study, extra)
        return self._export.to_message()

    @property
    def errors(self) -> Errors:
        return self._export.errors
