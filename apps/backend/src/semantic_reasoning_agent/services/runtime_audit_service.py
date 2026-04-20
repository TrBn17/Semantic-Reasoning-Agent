from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.runtime import (
    EvidenceRecordORM,
    TaskRunORM,
    ToolCallORM,
    WorkflowRunORM,
)
from semantic_reasoning_agent.domain.contracts.evidence import Evidence
from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolResult
from semantic_reasoning_agent.schemas.tasks import TaskRunRecord, WorkflowRunRecord
from semantic_reasoning_agent.schemas.tasks import ToolCallRecord


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeAuditService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def create_task_run(
        self,
        *,
        workspace_id: str,
        entrypoint: str,
        task_type: str,
        requested_output: str,
        input_payload: dict,
        conversation_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> str:
        now = _utc_now()
        task_id = str(uuid4())
        with self._database_manager.session() as session:
            session.add(
                TaskRunORM(
                    id=task_id,
                    workspace_id=workspace_id,
                    entrypoint=entrypoint,
                    task_type=task_type,
                    requested_output=requested_output,
                    status="running",
                    conversation_id=conversation_id,
                    provider=provider,
                    model=model,
                    input_payload=input_payload,
                    created_at=now,
                    started_at=now,
                    updated_at=now,
                )
            )
        return task_id

    def set_task_workflow(self, task_id: str, workflow_id: str) -> None:
        with self._database_manager.session() as session:
            task = session.get(TaskRunORM, task_id)
            if task is None:
                return
            task.workflow_id = workflow_id
            task.updated_at = _utc_now()

    def complete_task_run(
        self,
        task_id: str,
        *,
        status: str,
        output_payload: dict,
        provider: str | None = None,
        model: str | None = None,
        error_message: str | None = None,
    ) -> None:
        now = _utc_now()
        with self._database_manager.session() as session:
            task = session.get(TaskRunORM, task_id)
            if task is None:
                return
            task.status = status
            task.output_payload = output_payload
            task.provider = provider
            task.model = model
            task.error_message = error_message
            task.finished_at = now
            task.updated_at = now

    def create_workflow_run(
        self,
        *,
        task_id: str,
        workflow_id: str,
        workflow_version: str,
        input_payload: dict,
    ) -> str:
        now = _utc_now()
        run_id = str(uuid4())
        with self._database_manager.session() as session:
            session.add(
                WorkflowRunORM(
                    id=run_id,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    workflow_version=workflow_version,
                    status="running",
                    input_payload=input_payload,
                    created_at=now,
                    started_at=now,
                    updated_at=now,
                )
            )
        return run_id

    def complete_workflow_run(
        self,
        workflow_run_id: str,
        *,
        status: str,
        output_payload: dict,
        error_message: str | None = None,
    ) -> None:
        now = _utc_now()
        with self._database_manager.session() as session:
            run = session.get(WorkflowRunORM, workflow_run_id)
            if run is None:
                return
            run.status = status
            run.output_payload = output_payload
            run.error_message = error_message
            run.finished_at = now
            run.updated_at = now

    def record_tool_call(
        self,
        *,
        task_id: str | None,
        workflow_run_id: str | None,
        envelope: ToolEnvelope,
        result: ToolResult,
    ) -> None:
        if task_id is None:
            return
        tool_call_id = str(uuid4())
        with self._database_manager.session() as session:
            session.add(
                ToolCallORM(
                    id=tool_call_id,
                    task_id=task_id,
                    workflow_run_id=workflow_run_id,
                    call_id=str(envelope.call_id),
                    tool_name=envelope.tool_name,
                    status=result.status,
                    trace_id=result.meta.trace_id,
                    provider=result.meta.provider,
                    provider_version=result.meta.provider_version,
                    latency_ms=result.latency_ms,
                    input_payload={
                        "task_id": envelope.task_id,
                        "workflow_id": envelope.workflow_id,
                        "task_type": envelope.task_type,
                        "workspace_id": envelope.workspace_id,
                        "task_payload": dict(envelope.task_payload),
                        "arguments": dict(envelope.arguments),
                    },
                    output_payload={
                        "artifacts": [dict(item) for item in result.artifacts],
                        "state_patch": dict(result.state_patch),
                        "next_action_hints": list(result.next_action_hints),
                    },
                    error_code=result.error_code,
                    error_message=result.error_message,
                    created_at=result.started_at,
                    started_at=result.started_at,
                    finished_at=result.finished_at,
                )
            )
            for evidence in result.evidence:
                session.add(self._evidence_record(tool_call_id, task_id, evidence))

    def list_task_runs(self) -> list[TaskRunRecord]:
        with self._database_manager.session() as session:
            rows = session.scalars(select(TaskRunORM).order_by(desc(TaskRunORM.created_at))).all()
            return [
                TaskRunRecord(
                    id=row.id,
                    workspace_id=row.workspace_id,
                    entrypoint=row.entrypoint,
                    task_type=row.task_type,
                    requested_output=row.requested_output,
                    status=row.status,
                    workflow_id=row.workflow_id,
                    conversation_id=row.conversation_id,
                    provider=row.provider,
                    model=row.model,
                    error_message=row.error_message,
                    created_at=row.created_at,
                    started_at=row.started_at,
                    finished_at=row.finished_at,
                    updated_at=row.updated_at,
                    output_payload=row.output_payload or {},
                )
                for row in rows
            ]

    def get_task_run(self, task_id: str) -> TaskRunRecord | None:
        with self._database_manager.session() as session:
            row = session.get(TaskRunORM, task_id)
            if row is None:
                return None
            return TaskRunRecord(
                id=row.id,
                workspace_id=row.workspace_id,
                entrypoint=row.entrypoint,
                task_type=row.task_type,
                requested_output=row.requested_output,
                status=row.status,
                workflow_id=row.workflow_id,
                conversation_id=row.conversation_id,
                provider=row.provider,
                model=row.model,
                error_message=row.error_message,
                created_at=row.created_at,
                started_at=row.started_at,
                finished_at=row.finished_at,
                updated_at=row.updated_at,
                output_payload=row.output_payload or {},
            )

    def list_workflow_runs(self, task_id: str | None = None) -> list[WorkflowRunRecord]:
        with self._database_manager.session() as session:
            statement = select(WorkflowRunORM).order_by(desc(WorkflowRunORM.created_at))
            if task_id is not None:
                statement = statement.where(WorkflowRunORM.task_id == task_id)
            rows = session.scalars(statement).all()
            return [
                WorkflowRunRecord(
                    id=row.id,
                    task_id=row.task_id,
                    workflow_id=row.workflow_id,
                    workflow_version=row.workflow_version,
                    status=row.status,
                    created_at=row.created_at,
                    started_at=row.started_at,
                    finished_at=row.finished_at,
                    output_payload=row.output_payload or {},
                )
                for row in rows
            ]

    def list_tool_calls(self, task_id: str) -> list[ToolCallRecord]:
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(ToolCallORM)
                .where(ToolCallORM.task_id == task_id)
                .order_by(desc(ToolCallORM.created_at))
            ).all()
            return [
                ToolCallRecord(
                    id=row.id,
                    task_id=row.task_id,
                    workflow_run_id=row.workflow_run_id,
                    call_id=row.call_id,
                    tool_name=row.tool_name,
                    status=row.status,
                    trace_id=row.trace_id,
                    provider=row.provider,
                    provider_version=row.provider_version,
                    latency_ms=row.latency_ms,
                    error_code=row.error_code,
                    error_message=row.error_message,
                    created_at=row.created_at,
                    started_at=row.started_at,
                    finished_at=row.finished_at,
                    input_payload=row.input_payload or {},
                    output_payload=row.output_payload or {},
                )
                for row in rows
            ]

    @staticmethod
    def _evidence_record(tool_call_id: str, task_id: str, evidence: Evidence) -> EvidenceRecordORM:
        return EvidenceRecordORM(
            id=str(uuid4()),
            tool_call_id=tool_call_id,
            task_id=task_id,
            evidence_id=str(evidence.evidence_id),
            source_type=evidence.source_type,
            title=evidence.title,
            content=evidence.content,
            citation_anchor={
                "anchor_type": evidence.citation_anchor.anchor_type,
                "label": evidence.citation_anchor.label,
                "locator": evidence.citation_anchor.locator,
            },
            provenance={
                "workspace_id": evidence.provenance.workspace_id,
                "source_id": evidence.provenance.source_id,
                "tool_call_id": (
                    str(evidence.provenance.tool_call_id)
                    if evidence.provenance.tool_call_id is not None
                    else None
                ),
                "parser_version": evidence.provenance.parser_version,
                "extractor_version": evidence.provenance.extractor_version,
                "model": evidence.provenance.model,
                "captured_at": evidence.provenance.captured_at.isoformat(),
            },
            document_id=evidence.document_id,
            chunk_id=evidence.chunk_id,
            score=int(round(evidence.score * 1000)),
            trust_score=int(round(evidence.trust_score * 1000)),
        )
