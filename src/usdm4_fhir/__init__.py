from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from simple_error_log import Errors
from usdm4.api.study import Study
from usdm4_fhir.soa.export.export_soa import ExportSoA
from usdm4_fhir.m11.export.export_madrid import ExportMadrid
from usdm4_fhir.m11.export.export_prism2 import ExportPRISM2
from usdm4_fhir.m11.import_.import_prism2 import ImportPRISM2


class FHIRBase:
    def __init__(self):
        self._usdm = USDM4()
        self._export = None
        self._errors = None


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
        self._errors = self._export.errors
        return self._export.to_message()

    async def from_message(self, file_path: str, version: str = PRISM2) -> Wrapper | None:
        match version:
            case self.PRISM2:
                self._import = ImportPRISM2()
            case _:
                raise Exception(f"Version parameter '{version}' not recognized")
        self._errors = self._import.errors
        result: Wrapper = await self._import.from_message(file_path)
        return result

    @property
    def errors(self) -> Errors:
        return self._errors


class SoA(FHIRBase):
    def to_message(self, study: Study, extra: dict) -> str | None:
        self._export = ExportSoA(study, extra)
        return self._export.to_message()

    @property
    def errors(self) -> Errors:
        return self._export.errors
