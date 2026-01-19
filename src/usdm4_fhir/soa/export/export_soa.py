import datetime
from usdm4.api.study import Study
from usdm4.api.study_version import StudyVersion
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4_fhir.factory.identifier_factory import IdentifierFactory
from usdm4_fhir.factory.research_study_factory import ResearchStudyFactory
from usdm4_fhir.factory.bundle_factory import BundleFactory
from usdm4_fhir.factory.bundle_entry_factory import BundleEntryFactory
from usdm4_fhir.factory.timeline_plan_definition_factory import (
    TimelinePlanDefinitionFactory,
)
from usdm4_fhir.factory.timepoint_plan_definition_factory import (
    TimepointPlanDefinitionFactory,
)
from usdm4_fhir.factory.activity_definition_factory import ActivityDefinitionFactory
from usdm4_fhir.factory.urn_uuid import URNUUID
from usdm4_fhir.factory.study_url import StudyUrl
from simple_error_log.errors import Errors
from simple_error_log.error_location import KlassMethodLocation


class ExportSoA:
    MODULE = "usdm4_fhir.soa.export.Export"

    def __init__(self, study: Study, timeline_id: str, uuid: str, extra: dict = {}):
        """
        Initialize the ToFHIRSoA class
        """
        self._errors = Errors()
        self._study: Study = study
        self._extra: dict = extra
        self._study_version: StudyVersion = study.first_version()
        self._study_design: StudyDesign = self._study_version.studyDesigns[0]
        self._timeline: ScheduleTimeline = self._study_design.find_timeline(timeline_id)
        self._uuid = uuid

    @property
    def errors(self) -> Errors:
        return self._errors

    def to_message(self):
        """
        Build the FHIR SoA message
        """
        try:
            base_url = StudyUrl.generate(self._study)
            entries = []
            date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            identifier = IdentifierFactory(
                errors=self._errors,
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )

            # Add research study
            rs = ResearchStudyFactory(self._study, self._errors, self._extra)
            entries.append(
                BundleEntryFactory(
                    errors=self._errors,
                    request={
                        "method": "PUT",
                        "url": "ResearchStudy",
                    },
                    resource=rs.item,
                    fullUrl=URNUUID.generate(),
                ).item
            )

            # Add timeline plan definition, this is the overall timeline.
            tlpd = TimelinePlanDefinitionFactory(self._study, self._timeline, self._errors)
            entries.append(
                BundleEntryFactory(
                    errors=self._errors,
                    request={
                        "method": "PUT",
                        "url": "PlanDefinition",
                    },
                    resource=tlpd.item,
                    fullUrl=URNUUID.generate(),
                ).item
            )
            rs.item.protocol.append({"reference": f"PlanDefinition/{tlpd.item.id}"})

            # Add timepoint plan definitions for the activities
            for index, tp in enumerate(self._timeline.instances):
                tppd = TimepointPlanDefinitionFactory(
                    self._study, self._study_design, tp, self._errors
                )
                entries.append(
                    BundleEntryFactory(
                        errors=self._errors,
                        request={
                            "method": "PUT",
                            "url": "PlanDefinition",
                        },
                        resource=tppd.item,
                        fullUrl=URNUUID.generate(),
                    ).item
                )

            # Add activity definitions for each activit
            activity_list = self._study_design.activity_list()
            for index, activity in enumerate(activity_list):
                ad = ActivityDefinitionFactory(
                    errors=self._errors,
                    id=f"{ActivityDefinitionFactory.fix_id(activity.id)}",
                    name=activity.name,
                    title=activity.label_name(),
                    url=f"{base_url}/ActivityDefinition/{ActivityDefinitionFactory.fix_id(activity.name)}",
                    status="active",
                    description=activity.description,
                )
                entries.append(
                    BundleEntryFactory(
                        errors=self._errors,
                        request={
                            "method": "PUT",
                            "url": "ActivityDefinition",
                        },
                        resource=ad.item,
                        fullUrl=URNUUID.generate(),
                    ).item
                )

            # Build the final bundle
            bundle = BundleFactory(
                errors=self._errors,
                id=f"{BundleFactory.fix_id(self._study.name)}",
                entry=entries,
                type="transaction",
                identifier=identifier.item,
                timestamp=date,
            )
            return bundle.item.json()
        except Exception as e:
            location = KlassMethodLocation(self.MODULE, "to_message")
            self._errors.exception(
                "Exception raised building FHIR SoA message", e, location
            )
            return ""
