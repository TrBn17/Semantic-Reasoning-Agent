from fastapi import APIRouter, Depends, HTTPException, Query, status

from semantic_reasoning_agent.api.dependencies import get_ontology_service
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildCreateRequest,
    OntologyBuildResponse,
    OntologyCandidateEntityResponse,
    OntologyCandidateRelationResponse,
    OntologyGraphResponse,
    OntologyPublishResponse,
    OntologyReviewRequest,
    OntologyReviewStatus,
)
from semantic_reasoning_agent.services.ontology_service import (
    OntologyBuildError,
    OntologyBuildNotFoundError,
    OntologyCandidateNotFoundError,
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
