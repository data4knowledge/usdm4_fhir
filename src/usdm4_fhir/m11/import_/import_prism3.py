from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation
from usdm4.api.wrapper import Wrapper
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.researchstudy import ResearchStudy, ResearchStudyLabel
from fhir.resources.extension import Extension
from usdm4 import USDM4
from usdm4_fhir.__info__ import (
    __system_name__ as SYSTEM_NAME,
    __package_version__ as VERSION,
)


class ImportPRISM3:
    MODULE = "usdm4_fhir.m11.import_.import_prism2.ImportPRISM3"

    class LogicError(Exception):
        pass

    def __init__(self):
        self._errors: Errors = Errors()
        self._usdm4: USDM4 = USDM4()
        self._assembler = self._usdm4.assembler(self._errors)
        self._source_data = {}

    @property
    def errors(self) -> Errors:
        return self._errors

    async def from_message(self, filepath: str) -> Wrapper | None:
        try:
            data = self._read_file(filepath)
            self._source_data = self._from_fhir(data)
            print(f"ASSEMBLER DICT: {self._source_data}")
            self._assembler.execute(self._source_data)
            return self._assembler.wrapper(SYSTEM_NAME, VERSION)
        except Exception as e:
            self._errors.exception(
                "Exception raised parsing FHIR content",
                e,
                KlassMethodLocation(self.MODULE, "from_message"),
            )
            return None

    @property
    def extra(self):
        return {
            "title_page": {
                "compound_codes": "",
                "compound_names": "",
                "amendment_identifier": "",
                "sponsor_confidentiality": self._source_data["other"]["confidentiality"],
                "regulatory_agency_identifiers": "",
                # Those below not used?
                "amendment_details": "",
                "amendment_scope": "",
                "manufacturer_name_and_address": "",
                "medical_expert_contact": "",
                "original_protocol": "",
                "sae_reporting_method": "",
                "sponsor_approval_date": "",
                "sponsor_name_and_address": "",
                "sponsor_signatory": "",
            },
            "amendment": {
                "amendment_details": "",
                "robustness_impact": False,
                "robustness_impact_reason": "",
                "safety_impact": False,
                "safety_impact_reason": "",
            },
            "miscellaneous": {
                "medical_expert_contact": "",
                "sae_reporting_method": "",
                "sponsor_signatory": "",
            },
        }

    def _from_fhir(self, data: str) -> Wrapper:
        try:
            study = None
            bundle = Bundle.parse_raw(data)
            research_study: ResearchStudy = self._extract_from_bundle(bundle, ResearchStudy.__name__, first=True)
            if research_study:
                study = self._study(research_study)
            else:
                self._errors.warning(f"Failed to find ResearchStudy resource in the bundle.", KlassMethodLocation(self.MODULE, "_from_fhir"))
            return study
        except Exception as e:
            self._errors.exception(
                "Exception raised parsing FHIR message",
                e,
                KlassMethodLocation(self.MODULE, "_from_fhir"),
            )
            return None

    def _extract_from_bundle(self, bundle: Bundle, resource_type: str, first=False) -> list:
        try:
            results = []
            entry: BundleEntry
            for entry in bundle.entry:
                resource = entry.resource
                print(f"RESOURCE: {resource.resource_type} == {resource_type}")
                if resource.resource_type == resource_type:
                    return resource if first else results.append(resource)
            return None if first else results
        except Exception as e:
            self._errors.exception(
                "Exception raised extracting from Bundle",
                e,
                KlassMethodLocation(self.MODULE, "_extract_from_bundle"),
            )
            return None

    def _study(self, research_study: ResearchStudy) -> dict:
        try:
            acronym = self._extract_acronym(research_study.label)
            result = {
                "identification": {
                    "titles": {
                        "official": research_study.title,
                        "acronym": acronym,
                        "brief": self._extract_brief_title(research_study.label),
                    },
                    "identifiers": [
                        {
                            "identifier": "12345", # "identifier", <<<<<
                            "scope": {
                                "non_standard": {
                                    "type": "pharma",
                                    "description": "The sponsor organization",
                                    "label": "sponsor", # sponsor, <<<<<
                                    "identifier": "UNKNOWN",
                                    "identifierScheme": "UNKNOWN",
                                    "legalAddress": None, # address, <<<<<
                                }
                            },
                        }
                    ],
                },
                "compounds": {
                    "compound_codes": "", # <<<<<
                    "compound_names": "", # <<<<<
                },
                "amendments_summary": {
                    "amendment_identifier": "", # <<<<<
                    "amendment_scope": "", # <<<<<
                    "amendment_details": "", # <<<<<
                },
                "study_design": {
                    "label": "Study Design 1",
                    "rationale": "Not set",
                    "trial_phase": self._extract_phase(research_study.phase)
                },
                "study": {
                    "sponsor_approval_date": "", # <<<<<
                    "version_date": "", # <<<<<
                    "version": "1", # <<<<<
                    "rationale": "Not set",
                    "name": {
                        "acronym": acronym,
                        "identifier": "12345", # "identifier", <<<<<
                        "compound_code": "", # "compund code", <<<<<
                    },
                },
                "other": {
                    "confidentiality": self._extract_confidentiality_statement(research_study.extension),
                    "regulatory_agency_identifiers": "", # <<<<<
                },
                "document": {},
                #     "document": {
                #         "label": "Protocol Document",
                #         "version": "",  # @todo
                #         "status": "Final",  # @todo
                #         "template": "Legacy",
                #         "version_date": "",
                #     },
                #     "sections": []
                # },
                "population": {
                    "label": "Default population",
                    "inclusion_exclusion": {
                        "inclusion": [],
                        "exclusion": [],
                    },
                },
                "amendments": []
            }

            return result
        except Exception as e:
            self._errors.exception(
                "Exception raised assembling study information",
                e,
                KlassMethodLocation(self.MODULE, "__study")
            )
            return None

    def _extract_phase(self, phase: CodeableConcept) -> str:
        if phase.coding:
            coding: Coding = phase.coding[0]
            return coding.display
        self._errors.warning("Failed ot detect phase in ResearchStudy resource", KlassMethodLocation(self.MODULE, "_extract_phase"))
        return ""
    
    def _extract_acronym(self, labels) -> str:
        return self._extract_label(labels, "C207646")
    
    def _extract_brief_title(self, labels) -> str:
        return self._extract_label(labels, "C207615")

    def _extract_label(self, labels, type) -> str:
        if labels:
            label: ResearchStudyLabel
            for label in labels:
                if label.type.coding[0].code == type:
                    return label.value
        return ""

    def _extract_confidentiality_statement(self, extensions: list) -> str:
        ext = self._extract_extension(extensions, "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement")
        return ext.valueString if ext else ""
    
    def _extract_extension(self, extensions: list, url: str) -> Extension:
        item: ResearchStudyLabel
        for item in extensions:
            if item.url == url:
                return item
        return None

    def _read_file(self, full_path: str) -> dict:
        try:
            with open(full_path, "r") as f:
                data = f.read()
                f.close()
                return data
        except Exception as e:
            self._errors.exception(
                "Failed to read FHIR message file",
                e,
                KlassMethodLocation(self.MODULE, "_read_file"),
            )
