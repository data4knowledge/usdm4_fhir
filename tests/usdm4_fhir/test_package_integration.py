import json
import pytest
from tests.usdm4_fhir.helpers.files import read_yaml, write_json, read_json, write_yaml
from tests.usdm4_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from tests.usdm4_fhir.helpers.errors_clean import errors_clean_all
from usdm4_fhir import M11, SoA
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper


@pytest.fixture
def anyio_backend():
    return "asyncio"


SAVE = False


def run_to_m11_test(name, version, mode, save=False):
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_m11_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_m11_path(f"{name}_extra.yaml", version, mode))
    instance = M11()
    result = instance.to_message(study, extra, version)
    print(f"ERRORS:\n{instance.errors.dump(0)}")
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    error_filename = f"{name}_errors.yaml"
    if save:
        write_json(_full_m11_path(result_filename, version, mode), result)
        write_yaml(
            _full_m11_path(error_filename, version, mode),
            errors_clean_all(instance.errors),
        )
    expected = read_json(_full_m11_path(result_filename, version, mode))
    assert pretty_result == expected
    error_expected = read_yaml(_full_m11_path(error_filename, version, mode))
    assert errors_clean_all(instance.errors) == error_expected


async def run_from_m11_test(name: str, version: str, mode: str, save: bool = False):
    filename = f"{name}_fhir_m11.json"
    instance = M11()
    wrapper: Wrapper = await instance.from_message(
        _full_m11_path(filename, version, mode), version
    )
    print(f"ERRORS:\n{instance.errors.dump(0)}")
    result = wrapper.to_json()
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_usdm.json"
    error_filename = f"{name}_errors.yaml"
    if save:
        write_json(_full_m11_path(result_filename, version, mode), result)
        write_yaml(
            _full_m11_path(error_filename, version, mode),
            errors_clean_all(instance.errors),
        )
    expected = read_json(_full_m11_path(result_filename, version, mode))
    assert pretty_result == expected
    error_expected = read_yaml(_full_m11_path(error_filename, version, mode))
    assert errors_clean_all(instance.errors) == error_expected


def run_test_to_soa(name, save=False):
    version = ""
    mode = "export"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_soa_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_soa_path(f"{name}_extra.yaml", version, mode))
    study_version = study.first_version()
    study_design = study_version.studyDesigns[0]
    soa = SoA()
    result = soa.to_message(study, study_design.main_timeline().id, "FAKE-UUID", extra)
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_soa.json"
    if save:
        write_json(_full_soa_path(result_filename, version, mode), result)
    expected = read_json(_full_soa_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_soa_path(filename, version, mode):
    return f"tests/usdm4_fhir/test_files/soa/{mode}/{filename}"


def _full_m11_path(filename, version, mode):
    return f"tests/usdm4_fhir/test_files/m11/{mode}/{version}/{filename}"


def run_test_to_m11_prism3(name, save=False):
    version = "prism3"
    mode = "export"
    run_to_m11_test(name, version, mode, save)


async def run_test_from_m11_prism3(name, save=False):
    await run_from_m11_test(name, "prism3", "import", save)


# -----+-----


def test_to_fhir_prism3_asp8062():
    run_test_to_m11_prism3("ASP8063", SAVE)


@pytest.mark.anyio
async def test_from_fhir_prism3_asp8062():
    await run_test_from_m11_prism3("ASP8063", SAVE)


def test_to_fhir_soa_pilot():
    run_test_to_soa("pilot1", SAVE)
