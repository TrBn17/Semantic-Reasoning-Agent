from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from semantic_reasoning_agent.entrypoints.dependencies import get_document_service
from semantic_reasoning_agent.infrastructure.parsers.local_parser import UnsupportedDocumentTypeError
from semantic_reasoning_agent.schemas.documents import (
    DocumentBatchUploadResponse,
    DocumentJobResponse,
    DocumentReprocessResponse,
    DocumentResponse,
)
from semantic_reasoning_agent.services.document_service import (
    DocumentNotFoundError,
    DocumentProcessingError,
    DocumentService,
)


router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    workspace_id: str | None = Form(default=None),
    tags: str | None = Form(default=None),
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
        )
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DocumentProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/upload-batch", response_model=DocumentBatchUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    workspace_id: str | None = Form(default=None),
    tags: str | None = Form(default=None),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentBatchUploadResponse:
    parsed_tags = [tag.strip() for tag in tags.split(",")] if tags else []
    parsed_tags = [tag for tag in parsed_tags if tag]
    payload = []

    for file in files:
        try:
            payload.append((file.filename or "upload.bin", await file.read()))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return document_service.upload_documents(
        files=payload,
        workspace_id=workspace_id,
        tags=parsed_tags,
    )


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
