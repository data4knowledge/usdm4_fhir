import pytest
from tests.usdm_fhir.files.files import *
from tests.usdm_fhir.helpers.helpers import fix_uuid, fix_iso_dates
from usdm_fhir.soa.export.export import Export
from usdm4 import USDM4
from usdm4.api.study import *
from usdm4.api.study_design import *

SAVE = False


def _run_test_to(name, save=False):
    version = ""
    mode = "export"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    study_version = study.first_version()
    study_design = study_version.studyDesigns[0]
    result = Export(
        study, study_design.main_timeline().id, "FAKE-UUID", extra
    ).to_message()
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_soa.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_path(filename, version, mode):
    return f"tests/usdm_fhir/test_files/soa/{mode}/{filename}"


def test_from_fhir_v1_ASP8062():
    _run_test_to("pilot", SAVE)
