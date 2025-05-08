import datetime
from uuid import uuid4
from usdm4.api.eligibility_criterion import EligibilityCriterion
from usdm_fhir.m11.export.export_base import ExportBase
from usdm_fhir.m11.utility.soup import get_soup
from src.usdm_fhir.errors.errors import Location

from src.usdm_fhir.factory.base_factory import BaseFactory
from src.usdm_fhir.factory.research_study_factory import ResearchStudyFactory
from src.usdm_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from src.usdm_fhir.factory.reference_factory import ReferenceFactory
from src.usdm_fhir.factory.composition_factory import CompositionFactory
from src.usdm_fhir.factory.bundle_entry_factory import BundleEntryFactory
from src.usdm_fhir.factory.bundle_factory import BundleFactory
from src.usdm_fhir.factory.identifier_factory import IdentifierFactory
from src.usdm_fhir.factory.extension_factory import ExtensionFactory
from src.usdm_fhir.factory.group_factory import GroupFactory


class Export(ExportBase):
    MODULE = "src.usdm_fhir.m11.export.Export"

    class LogicError(Exception):
        pass

    def to_message(self) -> None:
        try:
            self._entries = []
            date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

            # Composition
            composition = self._composition_entry()
            self._add_bundle_entry(
                composition, "https://www.example.com/Composition/1234B"
            )

            # Research Study
            rs = ResearchStudyFactory(self.study)
            self._add_bundle_entry(rs, "https://www.example.com/Composition/1234A")

            # IE
            ie = self._inclusion_exclusion_critieria()
            self._add_bundle_entry(ie, "https://www.example.com/Composition/1234X1")

            # Final bundle
            identifier = IdentifierFactory(
                {"system": "urn:ietf:rfc:3986", "value": f"urn:uuid:{self._uuid}"}
            )
            bundle = BundleFactory(
                {
                    "id": None,
                    "entry": self._entries,
                    "type": "document",
                    "identifier": identifier.item,
                    "timestamp": date,
                }
            )
            return bundle.item.json()
        except Exception as e:
            self.errors.exception(
                "Exception raised generating FHIR content. See logs for more details",
                Location(self.MODULE, "export"),
                e,
            )
            return None

    def _add_bundle_entry(self, factory_item: BaseFactory, url: str):
        bundle_entry = BundleEntryFactory(
            {
                "item": factory_item.item,
                "url": url,
            }
        )
        self._entries.append(bundle_entry.item)

    def _composition_entry(self, sections, date):
        sections = self._create_narrative_sections()
        type_code = CodeableConceptFactory({"text": "EvidenceReport"}).item
        author = ReferenceFactory({"display": "USDM"}).item
        return CompositionFactory(
            {
                "title": self.doc_title,
                "type": type_code,
                "section": sections,
                "date": date,
                "status": "preliminary",
                "author": [author],
            }
        )

    def _create_narrative_sections(self):
        sections = []
        contents = self.protocol_document_version.narrative_content_in_order()
        for content in contents:
            section = self._content_to_section(content)
            if section:
                sections.append(section)
        return sections

    def _inclusion_exclusion_critieria(self):
        design = self.study_design
        criteria = design.criterion_map()
        all_of = self._extension_string(
            "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.combinationMethod",
            "all-of",
        )
        group = GroupFactory(
            {
                "id": str(uuid4()),
                "characteristic": [],
                "type": "person",
                "membership": "definitional",
                "extension": [all_of],
            }
        )
        for index, id in enumerate(design.population.criterionIds):
            criterion = criteria[id]
            self._criterion(criterion, group.item.characteristic)
        return group

    def _criterion(self, criterion: EligibilityCriterion, collection: list):
        version = self.study_version
        na = CodeableConceptFactory(
            {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "not-applicable",
                    }
                ]
            }
        )
        criterion_item = version.criterion_item(criterion.criterionItemId)
        if criterion_item:
            soup = get_soup(criterion_item.text)
            outer = self._extension_string(
                "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description",
                soup.get_text(),
            )
            exclude = True if criterion.category.code == "C25370" else False
            collection.append(
                {
                    "extension": outer.item,
                    "code": na.item,
                    "valueCodeableConcept": na.item,
                    "exclude": exclude,
                }
            )

    # def _recruitment(self, research_study: ResearchStudy, group_id):
    #     research_study.recruitment = {"eligibility": {"reference": f"Group/{group_id}"}}

    # def _estimands(self, research_study: ResearchStudy):
    #     version = self.study_version
    #     design = version.studyDesigns[0]
    #     for objective in self._primary_objectives():
    #         try:
    #             ext = self._extension_wrapper(
    #                 "http://example.org/fhir/extension/estimand"
    #             )
    #             id = self._treatment(research_study, objective["treatment"])
    #             pls_ext = self._extension_id(
    #                 "populationLevelSummary", self._fix_id(objective["summary"].id)
    #             )
    #             if pls_ext:
    #                 ext.extension.append(pls_ext)
    #             id = self._endpoint(research_study, objective["endpoint"])
    #             pls_ext = self._extension_id("endpoint-outcomeMeasure", id)
    #             if pls_ext:
    #                 ext.extension.append(pls_ext)
    #             pls_ext = self._extension_codeable_text(
    #                 "populationLevelSummary", objective["summary"].populationSummary
    #             )
    #             if pls_ext:
    #                 ext.extension.append(pls_ext)
    #             for ice in objective["events"]:
    #                 event_ext = self._extension_codeable_text("event", ice.description)
    #                 strategy_ext = self._extension_codeable_text("event", ice.strategy)
    #                 ice_ext = self._extension_wrapper("intercurrentEvent")
    #                 if ice_ext:
    #                     ice_ext.extension.append(event_ext)
    #                     ice_ext.extension.append(strategy_ext)
    #             item = {
    #                 "type": {"coding": CodingFactory({"usdm_code": objective["type"]})},
    #                 "description": objective["objective"].description,
    #                 "extension": [ext],
    #             }
    #             research_study.objective.append(item)
    #         except Exception as e:
    #             application_logger.exception("Exception in method _estimands", e)

    # def _treatment(
    #     self, research_study: ResearchStudy, treatment: USDMStudyIntervention
    # ):
    #     id = treatment.id
    #     item = {
    #         "linkId": self._fix_id(id),
    #         "name": "Treatment Group",
    #         "intendedExposure": {"display": treatment.description},
    #         "observedGroup": {"display": "Not Availabe"},
    #     }
    #     research_study.comparisonGroup.append(item)
    #     return id

    # def _endpoint(self, research_study: ResearchStudy, endpoint: USDMEndpoint):
    #     id = endpoint.id
    #     item = {
    #         "extension": [
    #             {
    #                 "url": "http://example.org/fhir/extension/linkId",
    #                 "valueId": self._fix_id(id),
    #             }
    #         ],
    #         "name": "Endpoint",
    #         "description": endpoint.text,
    #     }
    #     research_study.outcomeMeasure.append(item)
    #     return id

    # def _primary_objectives(self) -> list:
    #     return self._objective("C85826")

    # def _objective(self, type_code) -> list:
    #     results = []
    #     version = self.study_version
    #     design = version.studyDesigns[0]
    #     for objective in design.objectives:
    #         if objective.level.code == type_code:
    #             endpoint = objective.endpoints[0]  # Assuming only one for estimands?
    #             result = {
    #                 "objective": objective,
    #                 "type": objective.level,
    #                 "endpoint": objective.endpoints[0],
    #             }
    #             estimand = self._estimand_for(design, endpoint)
    #             if estimand:
    #                 result["population"] = self.study_design.find_analysis_population(
    #                     estimand.analysisPopulationId
    #                 )
    #                 # print(f"ESTIMAND ID: {estimand.interventionId}")
    #                 intervention = self.study_version.intervention(
    #                     estimand.interventionIds[0]
    #                 )
    #                 result["treatment"] = intervention if intervention else None
    #                 result["summary"] = estimand
    #                 result["events"] = []
    #                 for event in estimand.intercurrentEvents:
    #                     result["events"].append(event)
    #             # print(f"OBJECIVE: {result}")
    #             results.append(result)
    #     # print(f"OBJECIVE: {results[0].keys()}")
    #     return results

    # def _estimand_for(self, design: USDMStudyDesign, endpoint: USDMEndpoint):
    #     return next(
    #         (x for x in design.estimands if x.variableOfInterestId == endpoint.id), None
    #     )

    # def _organization_from_organization(self, organization: USDMOrganization):
    #     # print(f"ORG: {organization}")
    #     address = self._address_from_address(organization.legalAddress)
    #     name = organization.label if organization.label else organization.name
    #     return FHIROrganization(
    #         id=str(uuid4()), name=name, contact=[{"address": address}]
    #     )

    # def _address_from_address(self, address: USDMAddress):
    #     x = dict(address)
    #     x.pop("instanceType")
    #     y = {}
    #     for k, v in x.items():
    #         if v:
    #             y[k] = v
    #     if "lines" in y:
    #         y["line"] = y["lines"]
    #         y.pop("lines")
    #     if "country" in y:
    #         y["country"] = address.country.decode
    #     result = AddressType(y)
    #     # print(f"ADDRESS: {result}")
    #     return result

    # def _associated_party(self, value: str, role_code: str, role_display: str):
    #     if value:
    #         code = Coding(
    #             system="http://hl7.org/fhir/research-study-party-role",
    #             code=role_code,
    #             display=role_display,
    #         )
    #         role = CodeableConcept(coding=[code])
    #         return ResearchStudyAssociatedParty(role=role, party={"display": value})
    #     else:
    #         return None

    # def _associated_party_reference(
    #     self, reference: str, role_code: str, role_display: str
    # ):
    #     if reference:
    #         code = Coding(
    #             system="http://hl7.org/fhir/research-study-party-role",
    #             code=role_code,
    #             display=role_display,
    #         )
    #         role = CodeableConcept(coding=[code])
    #         return ResearchStudyAssociatedParty(
    #             role=role, party={"reference": reference}
    #         )
    #     else:
    #         return None

    # def _progress_status(self, value: str, state_code: str, state_display: str):
    #     # print(f"DATE: {value}")
    #     if value:
    #         code = Coding(
    #             system="http://hl7.org/fhir/research-study-party-role",
    #             code=state_code,
    #             display=state_display,
    #         )
    #         state = CodeableConcept(coding=[code])
    #         return ResearchStudyProgressStatus(state=state, period={"start": value})
    #     else:
    #         return None

    # def _amendment_ext(self, version: USDMStudyVersion):
    #     if len(version.amendments) == 0:
    #         return None
    #     source = version.amendments[0]
    #     amendment = Extension(
    #         url="http://example.org/fhir/extension/studyAmendment", extension=[]
    #     )
    #     ext = self._extension_string(
    #         "amendmentNumber", value=self._title_page["amendment_identifier"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_string("scope", value=self._title_page["amendment_scope"])
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_string(
    #         "details", value=self._title_page["amendment_details"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_boolean(
    #         "substantialImpactSafety", value=self._amendment["safety_impact"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_string(
    #         "substantialImpactSafety", value=self._amendment["safety_impact_reason"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_boolean(
    #         "substantialImpactSafety", value=self._amendment["robustness_impact"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     ext = self._extension_string(
    #         "substantialImpactSafety", value=self._amendment["robustness_impact_reason"]
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #     primary = CodeableConceptFactory(coding=CodingFactory({"usdm_code": source.primaryReason.code}).item)
    #     ext = self._extension_codeable(
    #         "http://hl7.org/fhir/uv/ebm/StructureDefinition/primaryReason",
    #         value=primary,
    #     )
    #     if ext:
    #         amendment.extension.append(ext)
    #         secondary = CodeableConceptFactory(coding=CodingFactory({"usdm_code": source.secondaryReasons[0].code}).item)
    #         ext = self._extension_codeable(
    #             "http://hl7.org/fhir/uv/ebm/StructureDefinition/secondaryReason",
    #             value=secondary,
    #         )
    #         if ext:
    #             amendment.extension.append(ext)
    #     return amendment

    # def _extension_wrapper(self, url):
    #     return Extension(url=url, extension=[])

    def _extension_string(self, url: str, value: str):
        return ExtensionFactory({"url": url, "valueString": value}) if value else None
        # return Extension(url=url, valueString=value) if value else None

    # def _extension_boolean(self, url: str, value: str):
    #     return Extension(url=url, valueBoolean=value) if value else None

    # def _extension_codeable(self, url: str, value: CodeableConcept):
    #     return Extension(url=url, valueCodeableConcept=value) if value else None

    # def _extension_codeable_text(self, url: str, value: str):
    #     return Extension(url=url, valueString=value) if value else None

    # def _extension_markdown_wrapper(self, url, value, ext):
    #     return Extension(url=url, extension=[ext]) if value else None

    # def _extension_markdown_wrapper_2(self, url, value, ext):
    #     return Extension(url=url, valueString=value)

    # def _extension_markdown(self, url, value):
    #     return Extension(url=url, valueMarkdown=value) if value else None

    def _extension_id(self, url: str, value: str):
        value = self.fix_id(value)
        return ExtensionFactory({"url": url, "valueId": value})
        # return Extension(url=url, valueId=value) if value else None

    # def _fix_id(self, value: str) -> str:
    #     return value.replace("_", "-")
