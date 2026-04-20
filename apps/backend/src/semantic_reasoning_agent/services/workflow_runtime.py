from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from semantic_reasoning_agent.schemas.tasks import WorkflowSpecSchema
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService

WorkflowMode = Literal["deterministic", "agentic"]


@dataclass(frozen=True)
class WorkflowSpec:
    workflow_id: str
    version: str
    mode: WorkflowMode
    description: str

    def to_schema(self) -> WorkflowSpecSchema:
        return WorkflowSpecSchema(
            workflow_id=self.workflow_id,
            version=self.version,
            mode=self.mode,
            description=self.description,
        )


class WorkflowRegistry:
    def __init__(self, specs: list[WorkflowSpec]) -> None:
        self._specs = {spec.workflow_id: spec for spec in specs}

    def get(self, workflow_id: str) -> WorkflowSpec | None:
        return self._specs.get(workflow_id)

    def list(self) -> list[WorkflowSpec]:
        return sorted(self._specs.values(), key=lambda spec: spec.workflow_id)


class WorkflowRuntime:
    def __init__(self, registry: WorkflowRegistry, audit_service: RuntimeAuditService) -> None:
        self._registry = registry
        self._audit_service = audit_service

    def list_workflows(self) -> list[WorkflowSpec]:
        return self._registry.list()

    def start_run(self, *, task_id: str, workflow_id: str, input_payload: dict) -> tuple[str, WorkflowSpec]:
        spec = self._registry.get(workflow_id)
        if spec is None:
            raise ValueError(f"Workflow '{workflow_id}' is not registered.")
        run_id = self._audit_service.create_workflow_run(
            task_id=task_id,
            workflow_id=spec.workflow_id,
            workflow_version=spec.version,
            input_payload=input_payload,
        )
        self._audit_service.set_task_workflow(task_id, spec.workflow_id)
        return run_id, spec

    def complete_run(
        self,
        workflow_run_id: str,
        *,
        status: str,
        output_payload: dict,
        error_message: str | None = None,
    ) -> None:
        self._audit_service.complete_workflow_run(
            workflow_run_id,
            status=status,
            output_payload=output_payload,
            error_message=error_message,
        )


def build_workflow_registry() -> WorkflowRegistry:
    return WorkflowRegistry(
        [
            WorkflowSpec(
                workflow_id="answer_resolution",
                version="1.0.0",
                mode="agentic",
                description="Resolve chat-style answer tasks via ontology grounding and tool use.",
            ),
            WorkflowSpec(
                workflow_id="document_ingestion",
                version="1.0.0",
                mode="deterministic",
                description="Process uploaded documents through parse, chunk, embed, and index steps.",
            ),
            WorkflowSpec(
                workflow_id="ontology_build",
                version="1.0.0",
                mode="deterministic",
                description="Build ontology candidates and reviewable graph state from workspace evidence.",
            ),
            WorkflowSpec(
                workflow_id="review_publish",
                version="1.0.0",
                mode="deterministic",
                description="Publish approved ontology state and sync the graph projection.",
            ),
        ]
    )
