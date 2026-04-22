from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.entrypoints.dependencies import get_ontology_service
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyCandidateEntityUpdateRequest,
    OntologyCandidateEntityResponse,
    OntologyCandidateRelationUpdateRequest,
    OntologyCandidateRelationResponse,
    OntologyDraftPublishRequest,
    OntologyGraphResponse,
    OntologyGraphDraftNodeRequest,
    OntologyGraphDraftNodeUpdateRequest,
    OntologyGraphDraftRelationRequest,
    OntologyGraphDraftRelationUpdateRequest,
    OntologyGraphDraftResponse,
    OntologyEntityTypeDefinitionUpdateRequest,
    OntologyPublishPreviewResponse,
    OntologyPublishResponse,
    OntologyRelationTypeDefinitionUpdateRequest,
    OntologyReviewRequest,
    OntologyReviewStatus,
)
from semantic_reasoning_agent.services.ontology_service import (
    OntologyBuildError,
    OntologyBuildNotFoundError,
    OntologyCandidateNotFoundError,
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


@router.get("/builds/{build_id}/entities", response_model=list[OntologyCandidateEntityResponse])
def list_build_entities(
    build_id: str,
    review_status: OntologyReviewStatus | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> list[OntologyCandidateEntityResponse]:
    try:
        return ontology_service.list_build_entities(build_id, status=review_status)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/builds/{build_id}/relations", response_model=list[OntologyCandidateRelationResponse])
def list_build_relations(
    build_id: str,
    review_status: OntologyReviewStatus | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> list[OntologyCandidateRelationResponse]:
    try:
        return ontology_service.list_build_relations(build_id, status=review_status)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/entities/{entity_id}/review", response_model=OntologyCandidateEntityResponse)
def review_entity(
    entity_id: str,
    request: OntologyReviewRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyCandidateEntityResponse:
    try:
        return ontology_service.review_entity(entity_id, request.action)
    except OntologyCandidateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/entities/{entity_id}", response_model=OntologyCandidateEntityResponse)
def update_entity(
    entity_id: str,
    request: OntologyCandidateEntityUpdateRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyCandidateEntityResponse:
    try:
        return ontology_service.update_entity(entity_id, request)
    except OntologyCandidateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/relations/{relation_id}/review", response_model=OntologyCandidateRelationResponse)
def review_relation(
    relation_id: str,
    request: OntologyReviewRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyCandidateRelationResponse:
    try:
        return ontology_service.review_relation(relation_id, request.action)
    except OntologyCandidateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/relations/{relation_id}", response_model=OntologyCandidateRelationResponse)
def update_relation(
    relation_id: str,
    request: OntologyCandidateRelationUpdateRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyCandidateRelationResponse:
    try:
        return ontology_service.update_relation(relation_id, request)
    except OntologyCandidateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/builds/{build_id}/publish-preview", response_model=OntologyPublishPreviewResponse)
def preview_publish(
    build_id: str,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyPublishPreviewResponse:
    try:
        return ontology_service.preview_publish(build_id)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OntologyPublishError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/builds/{build_id}/publish", response_model=OntologyPublishResponse)
def publish_build(
    build_id: str,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyPublishResponse:
    try:
        return ontology_service.publish_build(build_id)
    except OntologyBuildNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OntologyPublishError as exc:
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


@router.post("/graph/draft/publish", response_model=OntologyPublishResponse)
def publish_graph_draft(
    request: OntologyDraftPublishRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyPublishResponse:
    try:
        return ontology_service.publish_graph_draft(request)
    except OntologyPublishError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
