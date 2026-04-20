from fastapi import APIRouter, Depends, HTTPException, status

from semantic_reasoning_agent.entrypoints.dependencies import (
    get_runtime_audit_service,
    get_task_runtime,
)
from semantic_reasoning_agent.schemas.tasks import (
    ToolCallRecord,
    TaskResolutionRequest,
    TaskResolutionResponse,
    TaskRunRecord,
)
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.runtime_errors import ProviderNotReadyError
from semantic_reasoning_agent.services.task_runtime import TaskRuntime

router = APIRouter()


@router.post("/resolve", response_model=TaskResolutionResponse, status_code=status.HTTP_201_CREATED)
def resolve_task(
    payload: TaskResolutionRequest,
    task_runtime: TaskRuntime = Depends(get_task_runtime),
) -> TaskResolutionResponse:
    try:
        return task_runtime.resolve(payload)
    except ProviderNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[TaskRunRecord])
def list_tasks(
    audit_service: RuntimeAuditService = Depends(get_runtime_audit_service),
) -> list[TaskRunRecord]:
    return audit_service.list_task_runs()


@router.get("/{task_id}", response_model=TaskRunRecord)
def get_task(
    task_id: str,
    audit_service: RuntimeAuditService = Depends(get_runtime_audit_service),
) -> TaskRunRecord:
    task = audit_service.get_task_run(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' was not found.")
    return task


@router.get("/{task_id}/tool-calls", response_model=list[ToolCallRecord])
def list_task_tool_calls(
    task_id: str,
    audit_service: RuntimeAuditService = Depends(get_runtime_audit_service),
) -> list[ToolCallRecord]:
    return audit_service.list_tool_calls(task_id)
