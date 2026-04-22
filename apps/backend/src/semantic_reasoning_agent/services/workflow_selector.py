from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.services.evidence_judge import SufficiencyResult
from semantic_reasoning_agent.services.ontology_grounding_service import OntologyGroundingResult
from semantic_reasoning_agent.services.task_interpreter import TaskInterpretation


@dataclass(frozen=True)
class WorkflowSelection:
    workflow_id: str
    reason: str


class WorkflowSelector:
    def select(
        self,
        *,
        interpretation: TaskInterpretation,
        grounding: OntologyGroundingResult,
        sufficiency: SufficiencyResult | None = None,
    ) -> WorkflowSelection:
        if sufficiency and sufficiency.state == "insufficient" and interpretation.use_internal_only:
            return WorkflowSelection(workflow_id="task.resolve.review", reason="insufficient_internal_evidence")
        if grounding.grounding_status == "ambiguous":
            return WorkflowSelection(workflow_id="task.resolve.review", reason="ambiguous_grounding")
        if interpretation.candidate_workflow_type == "dynamic_agentic":
            return WorkflowSelection(workflow_id="task.resolve.chat", reason="agentic_required")
        return WorkflowSelection(workflow_id="task.resolve.chat", reason="default_grounded_chat")
