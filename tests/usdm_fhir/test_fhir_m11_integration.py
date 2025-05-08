import pytest
from tests.usdm_fhir.files.files import *
from tests.usdm_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from src.usdm_fhir import USDMFHIR
# from app.usdm.fhir.from_fhir_v1 import FromFHIRV1
# from app.usdm.fhir.to_fhir_v1 import ToFHIRV1
# from app.usdm.fhir.to_fhir_v2 import ToFHIRV2
# from app.model.file_handling.data_files import DataFiles
from usdm4 import USDM4

SAVE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"

async def _run_test_to_v3(name, save=False):
    version = "v3"
    mode = "export"
    filename = f"{name}_usdm.json"
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    instance = USDMFHIR(_full_path(filename, version, mode, extra))
    result = instance.export()
    result = fix_iso_dates(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected

def _full_path(filename, version, mode):
    return f"tests/test_files/fhir_{version}/{mode}/{filename}"


@pytest.mark.anyio
async def test_to_fhir_v3_pilot():
    await _run_test_to_v3("pilot", SAVE)


@pytest.mark.anyio
async def test_to_fhir_v3_ASP8062():
    await _run_test_to_v3("ASP8062", SAVE)


