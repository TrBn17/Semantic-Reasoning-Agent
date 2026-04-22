from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from semantic_reasoning_agent.documents.errors import UnsupportedDocumentTypeError
from semantic_reasoning_agent.entrypoints.dependencies import get_document_service
from semantic_reasoning_agent.schemas.documents import (
    DocumentArtifactResponse,
    DocumentExtractRequest,
    DocumentIngestionCapabilitiesResponse,
    DocumentExtractionRunResponse,
    DocumentJobResponse,
    DocumentReprocessResponse,
    DocumentResponse,
)
from semantic_reasoning_agent.documents.service import (
    DocumentNotFoundError,
    DocumentProcessingError,
    DocumentService,
)


router = APIRouter()


@router.get("/options", response_model=DocumentIngestionCapabilitiesResponse)
def get_document_ingestion_options(
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentIngestionCapabilitiesResponse:
    return document_service.get_ingestion_capabilities()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    workspace_id: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    pdf_mode: str | None = Form(default=None),
    output_format: str | None = Form(default=None),
    extract_images: bool | None = Form(default=None),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    try:
        content = await file.read()
        parsed_tags = [tag.strip() for tag in tags.split(",")] if tags else []
        parsed_tags = [tag for tag in parsed_tags if tag]
        return document_service.upload_document(
            filename=file.filename or "upload.bin",
            content=content,
            title=title,
            workspace_id=workspace_id,
            tags=parsed_tags,
            pdf_mode=pdf_mode,
            output_format=output_format,
            extract_images=extract_images,
            content_type=file.content_type,
        )
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentResponse]:
    return document_service.list_documents()


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    try:
        return document_service.get_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{document_id}/jobs", response_model=list[DocumentJobResponse])
def get_document_jobs(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentJobResponse]:
    try:
        return document_service.get_document_jobs(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{document_id}/artifacts", response_model=list[DocumentArtifactResponse])
def list_document_artifacts(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> list[DocumentArtifactResponse]:
    try:
        return document_service.list_artifacts(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{document_id}/extract", response_model=DocumentExtractionRunResponse, status_code=status.HTTP_201_CREATED)
def extract_document(
    document_id: str,
    payload: DocumentExtractRequest,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExtractionRunResponse:
    try:
        return document_service.run_structured_extraction(document_id, payload)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{document_id}/extract/{run_id}", response_model=DocumentExtractionRunResponse)
def get_document_extraction_run(
    document_id: str,
    run_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentExtractionRunResponse:
    try:
        return document_service.get_extraction_run(document_id, run_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{document_id}/reprocess", response_model=DocumentReprocessResponse)
def reprocess_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentReprocessResponse:
    try:
        return document_service.reprocess_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
