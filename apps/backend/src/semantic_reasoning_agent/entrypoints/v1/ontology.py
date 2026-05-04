from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.core.config import get_settings
from semantic_reasoning_agent.entrypoints.dependencies import (
    get_ontology_graph_projection_service,
    get_ontology_service,
)
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyDraftPublishRequest,
    OntologyGraphResponse,
    OntologyGraphDraftNodeRequest,
    OntologyGraphDraftNodeUpdateRequest,
    OntologyGraphDraftRelationRequest,
    OntologyGraphDraftRelationUpdateRequest,
    OntologyGraphDraftResponse,
    OntologyEntityTypeDefinitionUpdateRequest,
    OntologyGraphProjectionCreateRequest,
    OntologyGraphProjectionResponse,
    OntologyPublishResponse,
    OntologyRelationTypeDefinitionUpdateRequest,
)
from semantic_reasoning_agent.services.ontology_graph_projection_service import (
    OntologyGraphProjectionError,
    OntologyGraphProjectionNotFoundError,
    OntologyGraphProjectionService,
)
from semantic_reasoning_agent.services.ontology_service import (
    OntologyBuildError,
    OntologyBuildNotFoundError,
    OntologyDraftError,
    OntologyGraphError,
    OntologyPublishError,
    OntologyService,
)


router = APIRouter()


@router.post("/builds", response_model=OntologyBuildResponse, status_code=status.HTTP_201_CREATED)
def create_build(
    request: OntologyBuildCreateRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyBuildResponse:
    try:
        return ontology_service.create_build(request)
    except OntologyBuildError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/builds", response_model=list[OntologyBuildResponse])
def list_builds(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> list[OntologyBuildResponse]:
    return ontology_service.list_builds(workspace_id=workspace_id)


@router.get("/builds/{build_id}", response_model=OntologyBuildResponse)
def get_build(
    build_id: str,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyBuildResponse:
    try:
        return ontology_service.get_build(build_id)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/builds/{build_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_build(
    build_id: str,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> None:
    try:
        ontology_service.delete_build(build_id)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OntologyBuildError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/graph", response_model=OntologyGraphResponse)
def get_graph(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphResponse:
    try:
        return ontology_service.get_graph(workspace_id=workspace_id)
    except OntologyGraphError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/graph/draft", response_model=OntologyGraphDraftResponse)
def get_graph_draft(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.get_graph_draft(workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/graph/draft/nodes", response_model=OntologyGraphDraftResponse)
def create_graph_draft_node(
    request: OntologyGraphDraftNodeRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.create_draft_node(request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/graph/draft/nodes/{node_id}", response_model=OntologyGraphDraftResponse)
def update_graph_draft_node(
    node_id: str,
    request: OntologyGraphDraftNodeUpdateRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.update_draft_node(node_id, request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/graph/draft/nodes/{node_id}", response_model=OntologyGraphDraftResponse)
def delete_graph_draft_node(
    node_id: str,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.delete_draft_node(node_id, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/graph/draft/relations", response_model=OntologyGraphDraftResponse)
def create_graph_draft_relation(
    request: OntologyGraphDraftRelationRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.create_draft_relation(request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/graph/draft/relations/{relation_id}", response_model=OntologyGraphDraftResponse)
def update_graph_draft_relation(
    relation_id: str,
    request: OntologyGraphDraftRelationUpdateRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.update_draft_relation(relation_id, request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/graph/draft/relations/{relation_id}", response_model=OntologyGraphDraftResponse)
def delete_graph_draft_relation(
    relation_id: str,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.delete_draft_relation(relation_id, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/graph/draft/entity-types/{type_id}", response_model=OntologyGraphDraftResponse)
def update_graph_draft_entity_type(
    type_id: str,
    request: OntologyEntityTypeDefinitionUpdateRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.update_draft_entity_type(type_id, request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/graph/draft/relation-types/{type_id}", response_model=OntologyGraphDraftResponse)
def update_graph_draft_relation_type(
    type_id: str,
    request: OntologyRelationTypeDefinitionUpdateRequest,
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    try:
        return ontology_service.update_draft_relation_type(type_id, request, workspace_id=workspace_id)
    except OntologyDraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/graph/draft/reset", response_model=OntologyGraphDraftResponse)
def reset_graph_draft(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphDraftResponse:
    return ontology_service.reset_graph_draft(workspace_id=workspace_id)


@router.get("/graph-projections", response_model=list[OntologyGraphProjectionResponse])
def list_graph_projections(
    workspace_id: str | None = Query(default=None),
    projection_service: OntologyGraphProjectionService = Depends(get_ontology_graph_projection_service),
) -> list[OntologyGraphProjectionResponse]:
    resolved = workspace_id or get_settings().default_workspace_id
    return projection_service.list_projections(resolved)


@router.post(
    "/graph-projections",
    response_model=OntologyGraphProjectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_graph_projection(
    request: OntologyGraphProjectionCreateRequest,
    projection_service: OntologyGraphProjectionService = Depends(get_ontology_graph_projection_service),
) -> OntologyGraphProjectionResponse:
    try:
        return projection_service.create_projection(request)
    except OntologyGraphProjectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/graph-projections/{projection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_graph_projection(
    projection_id: str,
    projection_service: OntologyGraphProjectionService = Depends(get_ontology_graph_projection_service),
) -> None:
    try:
        projection_service.delete_projection(projection_id)
    except OntologyGraphProjectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/graph/draft/publish", response_model=OntologyPublishResponse)
def publish_graph_draft(
    request: OntologyDraftPublishRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyPublishResponse:
    try:
        return ontology_service.publish_graph_draft(request)
    except OntologyPublishError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
