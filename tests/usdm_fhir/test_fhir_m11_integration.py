import json
from tests.usdm_fhir.files.files import read_yaml, write_json, read_json
from tests.usdm_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from usdm_fhir import M11
from usdm4 import USDM4

SAVE = True


def run_test_to_v3(name, save=False):
    version = "v3"
    mode = "export"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    # print(f"STUDY: {study}")
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    instance = M11()
    result = instance.to_m11(study, extra)
    print(f"ERRORS: {instance.errors()}")
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    # print(f"RESULT: {pretty_result}")
    result_filename = f"{name}_fhir_m11.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_path(filename, version, mode):
    return f"tests/usdm_fhir/test_files/m11/{mode}/{version}/{filename}"


def test_to_fhir_v3_test_1():
    run_test_to_v3("test_1", SAVE)


def test_to_fhir_v3_pilot():
    run_test_to_v3("pilot", SAVE)


def test_to_fhir_v3_ASP8062():
    run_test_to_v3("ASP8062", SAVE)
