import json
from tests.usdm_fhir.files.files import read_yaml, write_json, read_json
from tests.usdm_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from src.usdm_fhir import USDMFHIR

SAVE = False


def run_test_to_v3(name, save=False):
    version = "v3"
    mode = "export"
    filename = f"{name}_usdm.json"
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    instance = USDMFHIR()
    result = instance.to_m11(_full_path(filename, version, mode), extra)
    print(f"RESULT: {result}")
    result = fix_iso_dates(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_path(filename, version, mode):
    return f"tests/usdm_fhir/test_files/m11/{mode}/{version}/{filename}"


def test_to_fhir_v3_pilot():
    run_test_to_v3("pilot", SAVE)


def test_to_fhir_v3_ASP8062():
    run_test_to_v3("ASP8062", SAVE)
