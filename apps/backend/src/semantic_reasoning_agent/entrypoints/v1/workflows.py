from fastapi import APIRouter, Depends, HTTPException, status

from semantic_reasoning_agent.entrypoints.dependencies import get_task_runtime_service, get_workflow_registry_service
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.schemas.workflows import WorkflowSpecResponse
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService
from semantic_reasoning_agent.services.workflow_registry_service import WorkflowRegistryService


router = APIRouter()


@router.get("", response_model=list[WorkflowSpecResponse])
def list_workflows(
    workflow_registry: WorkflowRegistryService = Depends(get_workflow_registry_service),
) -> list[WorkflowSpecResponse]:
    return workflow_registry.list_workflows()


@router.post("/{workflow_id}/run", response_model=TaskResolveResponse)
def run_workflow(
    workflow_id: str,
    payload: TaskResolveRequest,
    task_runtime: TaskRuntimeService = Depends(get_task_runtime_service),
    workflow_registry: WorkflowRegistryService = Depends(get_workflow_registry_service),
) -> TaskResolveResponse:
    workflow_ids = {workflow.workflow_id for workflow in workflow_registry.list_workflows()}
    if workflow_id not in workflow_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_id}' is not registered.",
        )
    if workflow_id != "task.resolve.chat":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workflow '{workflow_id}' is not directly runnable via this endpoint yet.",
        )
    return task_runtime.resolve_api_request(payload)
