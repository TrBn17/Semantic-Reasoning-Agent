from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.entrypoints.dependencies import get_search_tool_service
from semantic_reasoning_agent.schemas.search_tools import (
    SearchToolConfigCreateRequest,
    SearchToolConfigResponse,
    SearchToolConfigUpdateRequest,
    SearchToolRunRequest,
    SearchToolRunResponse,
)
from semantic_reasoning_agent.services.search_tool_service import (
    SearchToolConfigInvalidError,
    SearchToolConfigNotFoundError,
    SearchToolConfigService,
)

from .route_metadata import PUBLIC_ROUTE

router = APIRouter()


@router.get(
    "",
    response_model=list[SearchToolConfigResponse],
    summary="List saved super-search configs",
    openapi_extra=PUBLIC_ROUTE,
)
def list_search_tools(
    workspace_id: str | None = Query(default=None),
    tool_type: Literal["docs", "graph"] | None = Query(default=None),
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> list[SearchToolConfigResponse]:
    return service.list(workspace_id=workspace_id, tool_type=tool_type)


@router.post(
    "",
    response_model=SearchToolConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a super-search config",
    openapi_extra=PUBLIC_ROUTE,
)
def create_search_tool(
    payload: SearchToolConfigCreateRequest,
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> SearchToolConfigResponse:
    try:
        return service.create(payload)
    except SearchToolConfigInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{config_id}",
    response_model=SearchToolConfigResponse,
    summary="Get a super-search config",
    openapi_extra=PUBLIC_ROUTE,
)
def get_search_tool(
    config_id: str,
    workspace_id: str | None = Query(default=None),
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> SearchToolConfigResponse:
    try:
        return service.get(config_id, workspace_id=workspace_id)
    except SearchToolConfigNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{config_id}",
    response_model=SearchToolConfigResponse,
    summary="Update a super-search config",
    openapi_extra=PUBLIC_ROUTE,
)
def update_search_tool(
    config_id: str,
    payload: SearchToolConfigUpdateRequest,
    workspace_id: str | None = Query(default=None),
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> SearchToolConfigResponse:
    try:
        return service.update(config_id, payload, workspace_id=workspace_id)
    except SearchToolConfigNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SearchToolConfigInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a super-search config",
    openapi_extra=PUBLIC_ROUTE,
)
def delete_search_tool(
    config_id: str,
    workspace_id: str | None = Query(default=None),
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> None:
    try:
        service.delete(config_id, workspace_id=workspace_id)
    except SearchToolConfigNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{config_id}/run",
    response_model=SearchToolRunResponse,
    summary="Run a saved super-search config",
    openapi_extra=PUBLIC_ROUTE,
)
def run_search_tool(
    config_id: str,
    payload: SearchToolRunRequest,
    workspace_id: str | None = Query(default=None),
    service: SearchToolConfigService = Depends(get_search_tool_service),
) -> SearchToolRunResponse:
    try:
        return service.run(config_id, payload, workspace_id=workspace_id)
    except SearchToolConfigNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
