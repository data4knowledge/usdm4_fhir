import json
import pytest
from tests.usdm4_fhir.helpers.files import read_yaml, write_json, read_json, write_yaml
from tests.usdm4_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from tests.usdm4_fhir.helpers.errors_clean import errors_clean_all
from usdm4_fhir.m11.export.export_madrid import ExportMadrid
from usdm4_fhir.m11.export.export_prism2 import ExportPRISM2
from usdm4_fhir.m11.export.export_prism3 import ExportPRISM3
from usdm4_fhir.m11.import_.import_prism2 import ImportPRISM2
from usdm4_fhir.m11.import_.import_prism3 import ImportPRISM3
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper


@pytest.fixture
def anyio_backend():
    return "asyncio"


SAVE = False


def get_export_instance(study, extra, version):
    if version == "madrid":
        return ExportMadrid(study, extra)
    elif version == "prism2":
        return ExportPRISM2(study, extra)
    elif version == "prism3":
        return ExportPRISM3(study, extra)
    else:
        return None


def get_import_instance(version):
    if version == "prism2":
        return ImportPRISM2()
    elif version == "prism3":
        return ImportPRISM3()
    else:
        return None


def run_to_test(name, version, mode, save=False):
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(full_path(f"{name}_extra.yaml", version, mode))
    instance = get_export_instance(study, extra, version)
    result = instance.to_message()
    print(f"ERRORS:\n{instance.errors.dump(0)}")
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir.json"
    error_filename = f"{name}_errors.yaml"
    if save:
        write_json(full_path(result_filename, version, mode), result)
        write_yaml(
            full_path(error_filename, version, mode), errors_clean_all(instance.errors)
        )
    expected = read_json(full_path(result_filename, version, mode))
    assert pretty_result == expected
    error_expected = read_yaml(full_path(error_filename, version, mode))
    assert errors_clean_all(instance.errors) == error_expected


async def run_from_test(name: str, version: str, mode: str, save: bool = False):
    filename = f"{name}_fhir.json"
    instance = get_import_instance(version)
    wrapper: Wrapper = await instance.from_message(
        full_path(filename, version, mode),
    )
    print(f"ERRORS:\n{instance.errors.dump(0)}")
    result = wrapper.to_json()
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_usdm.json"
    error_filename = f"{name}_errors.yaml"
    if save:
        write_json(full_path(result_filename, version, mode), result)
        write_yaml(
            full_path(error_filename, version, mode), errors_clean_all(instance.errors)
        )
    expected = read_json(full_path(result_filename, version, mode))
    assert pretty_result == expected
    error_expected = read_yaml(full_path(error_filename, version, mode))
    assert errors_clean_all(instance.errors) == error_expected


def run_test_to_prism2(name, save=False):
    version = "prism2"
    mode = "export"
    run_to_test(name, version, mode, save)


def run_test_to_madrid(name, save=False):
    version = "madrid"
    mode = "export"
    run_to_test(name, version, mode, save)


def run_test_to_prism3(name, save=False):
    version = "prism3"
    mode = "export"
    run_to_test(name, version, mode, save)


async def run_test_from_prism2(name, save=False):
    await run_from_test(name, "prism2", "import", save)


async def run_test_from_prism3(name, save=False):
    await run_from_test(name, "prism3", "import", save)


def full_path(filename, version, mode):
    return f"tests/usdm4_fhir/test_files/m11/{mode}/{version}/{filename}"


# TO FHIR TESTS
# =============


# PRISM2
def test_to_fhir_prism2_asp8062():
    run_test_to_prism2("ASP8062", SAVE)


def test_to_fhir_prism2_deucralip():
    run_test_to_prism2("DEUCRALIP", SAVE)


def test_to_fhir_prism2_igbj():
    run_test_to_prism2("IGBJ", SAVE)


def test_to_fhir_prism2_pilot():
    run_test_to_prism2("pilot", SAVE)


# Madrid
def test_to_fhir_madrid_asp8062():
    run_test_to_madrid("ASP8062", SAVE)


def test_to_fhir_madrid_igbj():
    run_test_to_madrid("IGBJ", SAVE)


def test_to_fhir_madrid_pilot():
    run_test_to_madrid("pilot", SAVE)


# PRISM3
def test_to_fhir_prism3_asp8062():
    run_test_to_prism3("ASP8062", SAVE)


def test_to_fhir_prism3_tcbcpt_01():
    run_test_to_prism3("TCBCPT_01", SAVE)


def test_to_fhir_prism3_tcbcpt_02():
    run_test_to_prism3("TCBCPT_02", SAVE)


def test_to_fhir_prism3_tcbcpt_03():
    run_test_to_prism3("TCBCPT_03", SAVE)


def test_to_fhir_prism3_wa42380():
    run_test_to_prism3("WA42380", SAVE)


# FROM FHIR TESTS
# ===============


# PRISM2
@pytest.mark.anyio
async def test_from_fhir_prism2_asp8062():
    await run_test_from_prism2("ASP8062", SAVE)


@pytest.mark.anyio
async def test_from_fhir_prism2_deucralipP():
    await run_test_from_prism2("DEUCRALIP", SAVE)


@pytest.mark.anyio
async def test_from_fhir_prism2_igbj():
    await run_test_from_prism2("IGBJ", SAVE)


# PRISM3
@pytest.mark.anyio
async def test_from_fhir_prism3_asp8062():
    await run_test_from_prism3("ASP8062", SAVE)


@pytest.mark.anyio
async def test_from_fhir_prism3_wa42380():
    await run_test_from_prism3("WA42380", SAVE)
