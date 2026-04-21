from fastapi import APIRouter, Depends

from semantic_reasoning_agent.entrypoints.dependencies import get_task_runtime_service
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest, TaskResolveResponse
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService


router = APIRouter()


@router.post("/resolve", response_model=TaskResolveResponse)
def resolve_task(
    payload: TaskResolveRequest,
    task_runtime: TaskRuntimeService = Depends(get_task_runtime_service),
) -> TaskResolveResponse:
    return task_runtime.resolve_api_request(payload)
