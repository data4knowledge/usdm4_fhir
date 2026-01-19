from simple_error_log import Errors
from usdm4_fhir.factory.base_factory import BaseFactory
from usdm4_fhir.factory.plan_definition_factory import PlanDefinitionFactory
from usdm4_fhir.factory.coding_factory import CodingFactory
from usdm4_fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm4_fhir.factory.plan_definition_action_factory import (
    PlanDefinitionActionFactory,
)
from usdm4.api.study import Study
from usdm4.api.study_design import StudyDesign
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
from usdm4_fhir.factory.study_url import StudyUrl


class TimepointPlanDefinitionFactory(BaseFactory):
    def __init__(
        self,
        study: Study,
        study_design: StudyDesign,
        timepoint: ScheduledDecisionInstance | ScheduledActivityInstance,
        errors: Errors,
    ):
        try:
            super.__init__(errors, **{})
            base_url = StudyUrl.generate(study)
            self.item = PlanDefinitionFactory(
                id=self.fix_id(timepoint.id),
                title=timepoint.label_name(),
                type=CodeableConceptFactory(
                    coding=[
                        CodingFactory(
                            code="clinical-protocol",
                            system="http://terminology.hl7.org/CodeSystem/plan-definition-type",
                        ).item
                    ]
                ).item,
                #       date=
                #       version=
                purpose=timepoint.description,
                status="active",
                url=f"{base_url}/PlanDefinition/{self.fix_id(timepoint.name)}",
                action=self._actions(study_design, timepoint, base_url),
            ).item
        except Exception as e:
            self.handle_exception(e)

    def _actions(
        self,
        study_design: StudyDesign,
        timepoint: ScheduledDecisionInstance | ScheduledActivityInstance,
        base_url: str,
    ) -> list:
        results = []
        activity_list = study_design.activity_list()
        activities = {v.id: v for v in activity_list}
        for id in timepoint.activityIds:
            activity = activities[id]
            action = PlanDefinitionActionFactory(
                id=self.fix_id(activity.id),
                title=activity.label_name(),
                definitionCanonical=f"{base_url}/ActivityDefinition/{self.fix_id(activity.name)}",
            )
            results.append(action.item)
        return results
