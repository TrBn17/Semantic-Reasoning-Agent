from __future__ import annotations

from semantic_reasoning_agent.core.runtime_constants import WORKFLOW_TASK_RESOLVE_CHAT
from semantic_reasoning_agent.schemas.workflows import WorkflowSpecResponse


class WorkflowRegistryService:
    def list_workflows(self) -> list[WorkflowSpecResponse]:
        return [
            WorkflowSpecResponse(
                workflow_id=WORKFLOW_TASK_RESOLVE_CHAT,
                name="Chat Task Resolution",
                description="Grounds a chat task across retrieval, ontology, and graph search before fallback.",
                deterministic=False,
            ),
            WorkflowSpecResponse(
                workflow_id="ontology.build",
                name="Ontology Build",
                description="Extracts candidate entities and relations from indexed workspace documents.",
                deterministic=True,
            ),
            WorkflowSpecResponse(
                workflow_id="ontology.publish",
                name="Ontology Publish",
                description="Publishes an approved ontology version and refreshes graph runtime indices.",
                deterministic=True,
            ),
        ]
