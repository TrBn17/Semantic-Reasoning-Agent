from fastapi import APIRouter, Depends, HTTPException, status

from semantic_reasoning_agent.entrypoints.dependencies import (
    get_runtime_audit_service,
    get_task_runtime,
    get_workflow_runtime,
)
from semantic_reasoning_agent.schemas.tasks import (
    TaskResolutionRequest,
    TaskResolutionResponse,
    WorkflowRunRecord,
    WorkflowSpecSchema,
)
from semantic_reasoning_agent.services.runtime_audit_service import RuntimeAuditService
from semantic_reasoning_agent.services.runtime_errors import ProviderNotReadyError
from semantic_reasoning_agent.services.task_runtime import TaskRuntime
from semantic_reasoning_agent.services.workflow_runtime import WorkflowRuntime

router = APIRouter()


@router.get("", response_model=list[WorkflowSpecSchema])
def list_workflows(
    workflow_runtime: WorkflowRuntime = Depends(get_workflow_runtime),
) -> list[WorkflowSpecSchema]:
    return [spec.to_schema() for spec in workflow_runtime.list_workflows()]


@router.get("/runs", response_model=list[WorkflowRunRecord])
def list_workflow_runs(
    audit_service: RuntimeAuditService = Depends(get_runtime_audit_service),
) -> list[WorkflowRunRecord]:
    return audit_service.list_workflow_runs()


@router.post("/{workflow_id}/run", response_model=TaskResolutionResponse, status_code=status.HTTP_201_CREATED)
def run_workflow(
    workflow_id: str,
    payload: TaskResolutionRequest,
    workflow_runtime: WorkflowRuntime = Depends(get_workflow_runtime),
    task_runtime: TaskRuntime = Depends(get_task_runtime),
) -> TaskResolutionResponse:
    workflows = workflow_runtime.list_workflows()
    spec = next((item for item in workflows if item.workflow_id == workflow_id), None)
    if spec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workflow '{workflow_id}' is not registered.")
    try:
        return task_runtime.resolve(payload)
    except ProviderNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
