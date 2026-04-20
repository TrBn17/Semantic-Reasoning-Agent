"""Consolidated knowledge-graph API (ingest → extract → publish, read, patch, delete)."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status

from semantic_reasoning_agent.entrypoints.dependencies import get_document_service, get_ontology_service
from semantic_reasoning_agent.infrastructure.parsers.local_parser import UnsupportedDocumentTypeError
from semantic_reasoning_agent.schemas.ontology import (
    KnowledgeGraphExtractRequest,
    KnowledgeGraphIngestResponse,
    KnowledgeGraphRelationPatch,
    OntologyGraphResponse,
    OntologyPublishResponse,
    OntologyRelationResponse,
)
from semantic_reasoning_agent.services.document_service import DocumentProcessingError, DocumentService
from semantic_reasoning_agent.services.ontology_service import (
    OntologyBuildError,
    OntologyGraphError,
    OntologyPublishError,
    OntologyRelationNotFoundError,
    OntologyService,
)

router = APIRouter()


@router.get("", response_model=OntologyGraphResponse)
def get_knowledge_graph(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyGraphResponse:
    try:
        return ontology_service.get_graph(workspace_id=workspace_id)
    except OntologyGraphError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/extract", response_model=OntologyPublishResponse, status_code=status.HTTP_200_OK)
def extract_and_publish(
    request: KnowledgeGraphExtractRequest,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyPublishResponse:
    try:
        return ontology_service.extract_sync_and_publish(
            document_id=request.document_id,
            workspace_id=request.workspace_id,
        )
    except OntologyBuildError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OntologyPublishError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/ingest", response_model=KnowledgeGraphIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_files_and_publish(
    files: list[UploadFile] = File(...),
    workspace_id: str | None = Form(default=None),
    document_service: DocumentService = Depends(get_document_service),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> KnowledgeGraphIngestResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required.",
        )
    doc_ids: list[str] = []
    for upload in files:
        try:
            content = await upload.read()
            doc = document_service.upload_document(
                filename=upload.filename or "upload.bin",
                content=content,
                workspace_id=workspace_id,
                enqueue_pipeline=False,
            )
        except UnsupportedDocumentTypeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except DocumentProcessingError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        doc_ids.append(doc.id)
    try:
        return ontology_service.ingest_documents_sync_publish(doc_ids, workspace_id=workspace_id)
    except OntologyBuildError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OntologyPublishError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/relations/{relation_id}", response_model=OntologyRelationResponse)
def patch_relation(
    relation_id: str,
    body: KnowledgeGraphRelationPatch,
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> OntologyRelationResponse:
    try:
        return ontology_service.patch_published_relation(relation_id, body)
    except OntologyRelationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except OntologyGraphError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_graph(
    workspace_id: str | None = Query(default=None),
    ontology_service: OntologyService = Depends(get_ontology_service),
) -> Response:
    try:
        ontology_service.delete_workspace_graph(workspace_id=workspace_id)
    except OntologyGraphError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
