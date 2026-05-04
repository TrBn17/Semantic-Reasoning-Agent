from __future__ import annotations

from uuid import uuid4

from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.runtime_audit import (
    EvidenceBundleORM,
    EvidenceConflictORM,
    OutputRouteORM,
    TaskRunORM,
    TaskRunStepORM,
    ToolCallAuditORM,
)


class RuntimeAuditService:
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def record_task_run(
        self,
        *,
        task_id: str,
        workspace_id: str,
        workflow_id: str,
        output_type: str,
        stop_reason: str,
        grounded: bool,
        content: str,
        trace: list[dict],
        tool_calls: list[dict],
        conflict_details: list[dict] | None = None,
    ) -> None:
        with self._database_manager.session() as session:
            session.add(
                TaskRunORM(
                    id=task_id,
                    workspace_id=workspace_id,
                    workflow_id=workflow_id,
                    output_type=output_type,
                    stop_reason=stop_reason,
                    grounded=grounded,
                    content=content,
                    created_at=utc_now(),
                )
            )
            # Parent row must exist before inserts into evidence_bundles / task_run_steps / …
            # (Session uses autoflush=False; PG validates FK immediately on each INSERT.)
            session.flush()
            for item in trace:
                session.add(
                    TaskRunStepORM(
                        id=str(uuid4()),
                        task_run_id=task_id,
                        stage=str(item.get("stage", "unknown")),
                        detail=item,
                        created_at=utc_now(),
                    )
                )
            for item in tool_calls:
                session.add(
                    ToolCallAuditORM(
                        id=str(uuid4()),
                        task_run_id=task_id,
                        tool_name=str(item.get("tool_name", "unknown")),
                        status=str(item.get("status", "unknown")),
                        latency_ms=int(item.get("latency_ms", 0) or 0),
                        payload=item,
                        created_at=utc_now(),
                    )
                )
            session.add(
                EvidenceBundleORM(
                    id=str(uuid4()),
                    task_run_id=task_id,
                    summary={"trace_count": len(trace), "tool_call_count": len(tool_calls)},
                    created_at=utc_now(),
                )
            )
            if conflict_details:
                for item in conflict_details:
                    session.add(
                        EvidenceConflictORM(
                            id=str(uuid4()),
                            task_run_id=task_id,
                            conflict_type=str(item.get("conflict_type", "unknown")),
                            severity=str(item.get("severity", "low")),
                            detail=str(item.get("detail", "")),
                            created_at=utc_now(),
                        )
                    )
            session.add(
                OutputRouteORM(
                    id=str(uuid4()),
                    task_run_id=task_id,
                    output_type=output_type,
                    reason=stop_reason,
                    grounded=grounded,
                    created_at=utc_now(),
                )
            )
