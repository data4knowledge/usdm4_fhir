import json
from tests.usdm4_fhir.helpers.files import read_yaml, write_json, read_json, write_yaml
from tests.usdm4_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from tests.usdm4_fhir.helpers.errors_clean import errors_clean_all
from usdm4_fhir import M11
from usdm4 import USDM4

SAVE = False


def run_test_to_madrid(name, save=False):
    version = "madrid"
    mode = "export"
    run_test(name, version, mode, save)


def run_test_to_prism2(name, save=False):
    version = "prism2"
    mode = "export"
    run_test(name, version, mode, save)

def run_test(name, version, mode, save=False):
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    instance = M11()
    result = instance.to_message(study, extra, version)
    print(f"ERRORS:\n{instance.errors.dump(0)}")
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    error_filename = f"{name}_errors.yaml"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
        write_yaml(_full_path(error_filename, version, mode), errors_clean_all(instance.errors))
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected
    error_expected = read_yaml(_full_path(error_filename, version, mode))
    assert errors_clean_all(instance.errors) == error_expected

def _full_path(filename, version, mode):
    return f"tests/usdm4_fhir/test_files/m11/{mode}/{version}/{filename}"


def test_to_fhir_prism2_asp8062():
    run_test_to_prism2("ASP8062", SAVE)


def test_to_fhir_prism2_deucralip():
    run_test_to_prism2("DEUCRALIP", SAVE)


def test_to_fhir_prism2_igbj():
    run_test_to_prism2("IGBJ", SAVE)


def test_to_fhir_prism2_deucralip():
    run_test_to_prism2("pilot", SAVE)


def test_to_fhir_madrid_asp8062():
    run_test_to_madrid("ASP8062", SAVE)


def test_to_fhir_madrid_igbj():
    run_test_to_madrid("IGBJ", SAVE)


def test_to_fhir_madrid_pilot():
    run_test_to_madrid("pilot", SAVE)
