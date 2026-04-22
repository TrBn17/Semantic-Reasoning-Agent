from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import selectinload

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.errors import (
    DocumentNotFoundError,
    DocumentProcessingError,
    UnsupportedDocumentTypeError,
)
from semantic_reasoning_agent.documents.models import DocumentIngestionOptions, ParsedDocument
from semantic_reasoning_agent.documents.parsers.registry import DocumentParserRegistry
from semantic_reasoning_agent.infrastructure.storage import build_object_store
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentArtifactORM,
    DocumentChunkORM,
    DocumentExtractionRunORM,
    DocumentJobORM,
    DocumentORM,
)
from semantic_reasoning_agent.ports.object_store import ObjectStorePort
from semantic_reasoning_agent.schemas.documents import (
    DocumentArtifactResponse,
    DocumentExtractRequest,
    DocumentIngestionCapabilitiesResponse,
    DocumentIngestionOptionsResponse,
    DocumentOptionChoice,
    DocumentExtractionRunResponse,
    DocumentJobResponse,
    DocumentReprocessResponse,
    DocumentResponse,
    DocumentStatus,
    JobStatus,
)
from semantic_reasoning_agent.services.retrieval_service import RetrievalService
from semantic_reasoning_agent.workers.task_dispatcher import TaskDispatcher


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


PIPELINE_JOB_NAMES = [
    "parse_document",
    "store_artifacts",
    "build_chunks",
    "index_chunks",
]


class DocumentService:
    """Orchestrates document upload, Marker conversion, artifact storage, and indexing."""

    def __init__(
        self,
        settings: Settings,
        parser_registry: DocumentParserRegistry,
        retrieval_service: RetrievalService,
        database_manager: DatabaseManager,
        task_dispatcher: TaskDispatcher,
        object_store: ObjectStorePort | None = None,
    ) -> None:
        self._settings = settings
        self._parser_registry = parser_registry
        self._retrieval_service = retrieval_service
        self._database_manager = database_manager
        self._task_dispatcher = task_dispatcher
        self._object_store = object_store or build_object_store(settings)

    def list_documents(self) -> list[DocumentResponse]:
        with self._database_manager.session() as session:
            documents = session.scalars(select(DocumentORM).order_by(desc(DocumentORM.updated_at))).all()
            return [self._to_document_schema(document) for document in documents]

    def get_document(self, document_id: str) -> DocumentResponse:
        with self._database_manager.session() as session:
            document = session.get(DocumentORM, document_id)
            if document is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            return self._to_document_schema(document)

    def get_ingestion_capabilities(self) -> DocumentIngestionCapabilitiesResponse:
        supported_types = sorted(self._parser_registry.supported_types())
        marker_supported_types = sorted(
            document_type for document_type in supported_types if document_type != "csv"
        )
        csv_supported_types = ["csv"] if "csv" in supported_types else []
        return DocumentIngestionCapabilitiesResponse(
            supported_types=supported_types,
            marker_supported_types=marker_supported_types,
            csv_supported_types=csv_supported_types,
            default_options=DocumentIngestionOptionsResponse(
                pdf_mode=self._settings.pdf_parser_default_mode,
                output_format="markdown",
                use_llm=False,
                force_ocr=self._settings.pdf_parser_default_mode == "accurate",
                strip_existing_ocr=False,
                extract_images=True,
            ),
            pdf_mode_options=[
                DocumentOptionChoice(
                    value="fast",
                    label="Fast",
                    description="Lower latency with lightweight extraction and fallback support.",
                ),
                DocumentOptionChoice(
                    value="accurate",
                    label="Accurate",
                    description="Force OCR-heavy extraction for scanned or layout-sensitive PDFs.",
                ),
            ],
            output_format_options=[
                DocumentOptionChoice(
                    value="markdown",
                    label="Markdown",
                    description="Best default for chunking, citations, and downstream artifacts.",
                ),
                DocumentOptionChoice(
                    value="html",
                    label="HTML",
                    description="Preserve more layout semantics in Marker output.",
                ),
                DocumentOptionChoice(
                    value="json",
                    label="JSON",
                    description="Prefer structured renderer output for debugging or inspection.",
                ),
                DocumentOptionChoice(
                    value="chunks",
                    label="Chunks",
                    description="Emit chunk-oriented output for ingestion-focused workflows.",
                ),
            ],
            supports_extract_images=True,
        )

    def get_document_jobs(self, document_id: str) -> list[DocumentJobResponse]:
        with self._database_manager.session() as session:
            document = session.scalar(
                select(DocumentORM).options(selectinload(DocumentORM.jobs)).where(DocumentORM.id == document_id)
            )
            if document is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            return [self._to_job_schema(job) for job in sorted(document.jobs, key=self._job_sort_key)]

    def list_artifacts(self, document_id: str) -> list[DocumentArtifactResponse]:
        with self._database_manager.session() as session:
            document = session.scalar(
                select(DocumentORM).options(selectinload(DocumentORM.artifacts)).where(DocumentORM.id == document_id)
            )
            if document is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            return [self._to_artifact_schema(artifact) for artifact in document.artifacts]

    def upload_document(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        workspace_id: str | None = None,
        tags: list[str] | None = None,
        pdf_mode: str | None = None,
        output_format: str | None = None,
        extract_images: bool | None = None,
        content_type: str | None = None,
    ) -> DocumentResponse:
        if not content:
            raise DocumentProcessingError("Uploaded file is empty.")
        if not self._parser_registry.supports(filename):
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{Path(filename).suffix.lower().lstrip('.')}'. "
                "Supported types: pdf, docx, xlsx, pptx, html, epub, image, csv."
            )

        document_type = Path(filename).suffix.lower().lstrip(".")
        ingestion_options = self._resolve_ingestion_options(
            document_type,
            pdf_mode=pdf_mode,
            output_format=output_format,
            extract_images=extract_images,
        )
        document_id = str(uuid4())
        resolved_workspace_id = workspace_id or self._settings.default_workspace_id
        timestamp = utc_now()
        stored_object = self._object_store.put_document_binary(
            document_id,
            filename,
            content,
            content_type=content_type,
        )
        document = DocumentORM(
            id=document_id,
            title=title or Path(filename).stem,
            filename=filename,
            workspace_id=resolved_workspace_id,
            document_type=document_type,
            status=DocumentStatus.uploaded.value,
            parser_version="pending",
            chunk_count=0,
            tags=tags or [],
            ingestion_options=ingestion_options.to_dict(),
            source_url=stored_object.public_url,
            source_object_key=stored_object.object_key,
            source_content_type=stored_object.content_type,
            size_bytes=stored_object.size_bytes,
            binary_content=content if self._settings.object_store_backend.lower() != "minio" else b"",
            created_at=timestamp,
            updated_at=timestamp,
            error_message=None,
        )
        with self._database_manager.session() as session:
            session.add(document)
            session.add_all(self._build_job_records(document_id))

        self._queue_document(document_id)
        return self.get_document(document_id)

    def reprocess_document(self, document_id: str) -> DocumentReprocessResponse:
        self._ensure_document_exists(document_id)
        self._prepare_reprocess(document_id)
        self._queue_document(document_id)
        return DocumentReprocessResponse(
            document=self.get_document(document_id),
            jobs=self.get_document_jobs(document_id),
        )

    def reprocess_documents(self, document_ids: list[str] | None = None) -> list[str]:
        target_ids = document_ids or self._list_document_ids()
        for document_id in target_ids:
            self._prepare_reprocess(document_id)
            self._queue_document(document_id)
        return target_ids

    def run_structured_extraction(
        self,
        document_id: str,
        payload: DocumentExtractRequest,
    ) -> DocumentExtractionRunResponse:
        document = self._get_document_record(document_id)
        parser = self._parser_registry.get_parser(document.filename)
        extractor = getattr(parser, "extract_structured", None)
        if extractor is None:
            raise DocumentProcessingError(
                f"Structured extraction is not supported for '{document.document_type}'."
            )

        binary_content = self._object_store.get_document_binary(
            document.id,
            document.source_object_key,
            fallback_content=document.binary_content,
        )
        run_id = str(uuid4())
        now = utc_now()
        with self._database_manager.session() as session:
            session.add(
                DocumentExtractionRunORM(
                    id=run_id,
                    document_id=document.id,
                    workspace_id=document.workspace_id,
                    status="running",
                    schema_json=payload.extraction_schema,
                    result_json=None,
                    parser_version=document.parser_version,
                    use_llm=payload.use_llm,
                    error_message=None,
                    created_at=now,
                    updated_at=now,
                )
            )

        try:
            existing_markdown = self._latest_artifact_text(document.id, "markdown")
            result = extractor(
                document.filename,
                binary_content,
                schema_json=payload.extraction_schema,
                use_llm=payload.use_llm,
                force_ocr=payload.force_ocr,
                strip_existing_ocr=payload.strip_existing_ocr,
                existing_markdown=existing_markdown,
            )
            if result.markdown:
                self._store_artifact(
                    document_id=document.id,
                    workspace_id=document.workspace_id,
                    artifact_type="extraction_markdown",
                    artifact_name=f"{run_id}.md",
                    content=result.markdown.encode("utf-8"),
                    content_type="text/markdown",
                    metadata={"extraction_run_id": run_id},
                )
            self._update_extraction_run(
                run_id,
                status="completed",
                result_json=result.result,
                parser_version=result.parser_version,
                error_message=None,
            )
        except Exception as exc:
            self._update_extraction_run(
                run_id,
                status="failed",
                result_json=None,
                parser_version=document.parser_version,
                error_message=str(exc),
            )
            raise DocumentProcessingError(str(exc)) from exc

        return self.get_extraction_run(document.id, run_id)

    def get_extraction_run(self, document_id: str, run_id: str) -> DocumentExtractionRunResponse:
        with self._database_manager.session() as session:
            run = session.scalar(
                select(DocumentExtractionRunORM).where(
                    DocumentExtractionRunORM.document_id == document_id,
                    DocumentExtractionRunORM.id == run_id,
                )
            )
            if run is None:
                raise DocumentNotFoundError(
                    f"Structured extraction run '{run_id}' was not found for document '{document_id}'."
                )
            return self._to_extraction_run_schema(run)

    def process_document(self, document_id: str) -> None:
        document = self._get_document_record(document_id)
        self._reset_jobs(document_id)
        self._retrieval_service.remove_document(document_id)
        options = DocumentIngestionOptions.from_dict(document.ingestion_options)

        try:
            self._mark_job_running(document_id, "parse_document")
            binary_content = self._object_store.get_document_binary(
                document.id,
                document.source_object_key,
                fallback_content=document.binary_content,
            )
            parsed_document = self._parser_registry.parse(
                document.filename,
                binary_content,
                document.title,
                options=options,
            )
            self._mark_job_completed(document_id, "parse_document")
            self._update_document_state(
                document_id,
                status=DocumentStatus.parsed.value,
                parser_version=parsed_document.parser_version,
                error_message=None,
            )

            self._mark_job_running(document_id, "store_artifacts")
            self._replace_artifacts(document, parsed_document)
            self._mark_job_completed(document_id, "store_artifacts")

            self._mark_job_running(document_id, "build_chunks")
            chunk_count = len(parsed_document.chunks)
            self._mark_job_completed(document_id, "build_chunks")

            self._mark_job_running(document_id, "index_chunks")
            document_schema = self._to_document_schema(document)
            indexed_chunks = self._retrieval_service.prepare_document_chunks(document_schema, parsed_document)
            self._retrieval_service.upsert_chunks(document_id, indexed_chunks)
            self._mark_job_completed(document_id, "index_chunks")

            self._update_document_state(
                document_id,
                status=DocumentStatus.indexed.value,
                parser_version=parsed_document.parser_version,
                chunk_count=chunk_count,
                error_message=None,
            )
        except UnsupportedDocumentTypeError as exc:
            self._mark_failed(document_id, self._active_job_name(document_id), str(exc))
            raise
        except Exception as exc:
            self._mark_failed(document_id, self._active_job_name(document_id), str(exc))
            raise DocumentProcessingError(str(exc)) from exc

    def _resolve_ingestion_options(
        self,
        document_type: str,
        *,
        pdf_mode: str | None,
        output_format: str | None,
        extract_images: bool | None,
    ) -> DocumentIngestionOptions:
        requested_format = (output_format or "markdown").lower()
        if requested_format not in {"markdown", "html", "json", "chunks"}:
            raise DocumentProcessingError(
                "output_format must be one of 'markdown', 'html', 'json', or 'chunks'."
            )
        resolved_extract_images = True if extract_images is None else extract_images
        if document_type == "csv":
            return DocumentIngestionOptions()
        if document_type != "pdf":
            return DocumentIngestionOptions(
                output_format=requested_format,
                extract_images=resolved_extract_images,
            )
        requested_mode = (pdf_mode or self._settings.pdf_parser_default_mode).lower()
        if requested_mode not in {"fast", "accurate"}:
            raise DocumentProcessingError("pdf_mode must be either 'fast' or 'accurate'.")
        return DocumentIngestionOptions(
            pdf_mode=requested_mode,
            output_format=requested_format,
            force_ocr=requested_mode == "accurate",
            use_llm=requested_mode == "accurate" and self._settings.marker_use_llm_in_accurate,
            extract_images=resolved_extract_images,
        )

    def _mark_failed(self, document_id: str, failed_job: str, error_message: str) -> None:
        timestamp = utc_now()
        self._retrieval_service.remove_document(document_id)
        with self._database_manager.session() as session:
            row = session.get(DocumentORM, document_id)
            if row is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            row.status = DocumentStatus.failed.value
            row.error_message = error_message
            row.updated_at = timestamp
            row.chunk_count = 0
            self._update_failed_jobs(session, document_id, failed_job, error_message, timestamp)

    def _ensure_document_exists(self, document_id: str) -> None:
        with self._database_manager.session() as session:
            if session.get(DocumentORM, document_id) is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")

    def _get_document_record(self, document_id: str) -> DocumentORM:
        with self._database_manager.session() as session:
            document = session.get(DocumentORM, document_id)
            if document is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            return DocumentORM(
                id=document.id,
                title=document.title,
                filename=document.filename,
                workspace_id=document.workspace_id,
                document_type=document.document_type,
                status=document.status,
                parser_version=document.parser_version,
                chunk_count=document.chunk_count,
                tags=document.tags,
                ingestion_options=document.ingestion_options or {},
                source_url=document.source_url,
                source_object_key=document.source_object_key,
                source_content_type=document.source_content_type,
                size_bytes=document.size_bytes,
                binary_content=document.binary_content,
                created_at=document.created_at,
                updated_at=document.updated_at,
                error_message=document.error_message,
            )

    def _list_document_ids(self) -> list[str]:
        with self._database_manager.session() as session:
            return list(session.scalars(select(DocumentORM.id)).all())

    def _prepare_reprocess(self, document_id: str) -> None:
        with self._database_manager.session() as session:
            row = session.get(DocumentORM, document_id)
            if row is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            row.status = DocumentStatus.uploaded.value
            row.error_message = None
            row.chunk_count = 0
            row.updated_at = utc_now()
            session.execute(delete(DocumentChunkORM).where(DocumentChunkORM.document_id == document_id))
            session.execute(delete(DocumentJobORM).where(DocumentJobORM.document_id == document_id))
            session.execute(delete(DocumentArtifactORM).where(DocumentArtifactORM.document_id == document_id))
            session.execute(delete(DocumentExtractionRunORM).where(DocumentExtractionRunORM.document_id == document_id))
            session.add_all(self._build_job_records(document_id))

    def _queue_document(self, document_id: str) -> None:
        try:
            self._task_dispatcher.enqueue_document_processing(document_id)
        except Exception as exc:
            raise DocumentProcessingError(f"Failed to queue document '{document_id}' for ingestion.") from exc

    def _reset_jobs(self, document_id: str) -> None:
        with self._database_manager.session() as session:
            jobs = session.scalars(select(DocumentJobORM).where(DocumentJobORM.document_id == document_id)).all()
            if not jobs:
                session.add_all(self._build_job_records(document_id))
                return
            for job in jobs:
                job.status = JobStatus.pending.value
                job.started_at = None
                job.finished_at = None
                job.error_message = None

    def _mark_job_running(self, document_id: str, name: str) -> None:
        with self._database_manager.session() as session:
            job = self._get_job(session, document_id, name)
            now = utc_now()
            job.status = JobStatus.running.value
            job.started_at = now
            job.finished_at = None
            job.error_message = None

    def _mark_job_completed(self, document_id: str, name: str) -> None:
        with self._database_manager.session() as session:
            job = self._get_job(session, document_id, name)
            now = utc_now()
            job.status = JobStatus.completed.value
            if job.started_at is None:
                job.started_at = now
            job.finished_at = now
            job.error_message = None

    def _update_document_state(
        self,
        document_id: str,
        *,
        status: str,
        parser_version: str | None = None,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        with self._database_manager.session() as session:
            row = session.get(DocumentORM, document_id)
            if row is None:
                raise DocumentNotFoundError(f"Document '{document_id}' was not found.")
            row.status = status
            row.updated_at = utc_now()
            row.error_message = error_message
            if parser_version is not None:
                row.parser_version = parser_version
            if chunk_count is not None:
                row.chunk_count = chunk_count

    def _replace_artifacts(self, document: DocumentORM, parsed_document: ParsedDocument) -> None:
        with self._database_manager.session() as session:
            session.execute(delete(DocumentArtifactORM).where(DocumentArtifactORM.document_id == document.id))
        artifacts = list(parsed_document.artifacts)
        if not artifacts:
            markdown = "\n\n".join(chunk.text for chunk in parsed_document.chunks if chunk.text.strip())
            if markdown:
                artifacts.append(
                    type("InlineArtifact", (), {
                        "artifact_type": "markdown",
                        "name": "document.md",
                        "content": markdown.encode("utf-8"),
                        "content_type": "text/markdown",
                        "metadata": {},
                    })()
                )
            artifacts.append(
                type("InlineArtifact", (), {
                    "artifact_type": "normalized_json",
                    "name": "document.json",
                    "content": json.dumps(
                        {
                            "document_type": parsed_document.document_type,
                            "parser_name": parsed_document.parser_name,
                            "parser_version": parsed_document.parser_version,
                            "chunks": [chunk.text for chunk in parsed_document.chunks],
                        },
                        ensure_ascii=False,
                    ).encode("utf-8"),
                    "content_type": "application/json",
                    "metadata": {},
                })()
            )
        for artifact in artifacts:
            self._store_artifact(
                document_id=document.id,
                workspace_id=document.workspace_id,
                artifact_type=artifact.artifact_type,
                artifact_name=artifact.name,
                content=artifact.content,
                content_type=artifact.content_type,
                metadata=artifact.metadata,
            )

    def _store_artifact(
        self,
        *,
        document_id: str,
        workspace_id: str,
        artifact_type: str,
        artifact_name: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        stored = self._object_store.put_artifact_binary(
            document_id,
            artifact_name,
            content,
            content_type=content_type,
            artifact_type=artifact_type,
        )
        with self._database_manager.session() as session:
            session.add(
                DocumentArtifactORM(
                    id=str(uuid4()),
                    document_id=document_id,
                    workspace_id=workspace_id,
                    artifact_type=artifact_type,
                    name=artifact_name,
                    object_key=stored.object_key,
                    public_url=stored.public_url,
                    content_type=content_type,
                    size_bytes=stored.size_bytes,
                    metadata_json=metadata or {},
                    created_at=utc_now(),
                )
            )

    def _latest_artifact_text(self, document_id: str, artifact_type: str) -> str | None:
        with self._database_manager.session() as session:
            artifact = session.scalar(
                select(DocumentArtifactORM)
                .where(
                    DocumentArtifactORM.document_id == document_id,
                    DocumentArtifactORM.artifact_type == artifact_type,
                )
                .order_by(desc(DocumentArtifactORM.created_at))
            )
            if artifact is None:
                return None
        content = self._object_store.get_document_binary(document_id, artifact.object_key)
        return content.decode("utf-8") if content else None

    def _update_extraction_run(
        self,
        run_id: str,
        *,
        status: str,
        result_json: dict[str, object] | None,
        parser_version: str | None,
        error_message: str | None,
    ) -> None:
        with self._database_manager.session() as session:
            run = session.get(DocumentExtractionRunORM, run_id)
            if run is None:
                raise DocumentNotFoundError(f"Structured extraction run '{run_id}' was not found.")
            run.status = status
            run.result_json = result_json
            run.parser_version = parser_version
            run.error_message = error_message
            run.updated_at = utc_now()

    def _active_job_name(self, document_id: str) -> str:
        with self._database_manager.session() as session:
            jobs = session.scalars(select(DocumentJobORM).where(DocumentJobORM.document_id == document_id)).all()
            for name in reversed(PIPELINE_JOB_NAMES):
                for job in jobs:
                    if job.name == name and job.status == JobStatus.running.value:
                        return name
        return PIPELINE_JOB_NAMES[0]

    @staticmethod
    def _build_job_records(document_id: str) -> list[DocumentJobORM]:
        return [
            DocumentJobORM(
                id=f"{document_id}:{name}",
                document_id=document_id,
                name=name,
                status=JobStatus.pending.value,
                started_at=None,
                finished_at=None,
                error_message=None,
            )
            for name in PIPELINE_JOB_NAMES
        ]

    @staticmethod
    def _update_failed_jobs(
        session,
        document_id: str,
        failed_job: str,
        error_message: str,
        timestamp: datetime,
    ) -> None:
        jobs = session.scalars(select(DocumentJobORM).where(DocumentJobORM.document_id == document_id)).all()
        job_map = {job.name: job for job in jobs}
        failure_reached = False
        for name in PIPELINE_JOB_NAMES:
            job = job_map.get(name)
            if job is None:
                job = DocumentJobORM(
                    id=f"{document_id}:{name}",
                    document_id=document_id,
                    name=name,
                    status=JobStatus.pending.value,
                    started_at=None,
                    finished_at=None,
                    error_message=None,
                )
                session.add(job)
            if name == failed_job:
                failure_reached = True
                job.status = JobStatus.failed.value
                job.started_at = timestamp
                job.finished_at = timestamp
                job.error_message = error_message
            elif failure_reached:
                job.status = JobStatus.pending.value
                job.started_at = None
                job.finished_at = None
                job.error_message = None
            else:
                job.status = JobStatus.completed.value
                job.started_at = timestamp
                job.finished_at = timestamp
                job.error_message = None

    @staticmethod
    def _to_document_schema(document: DocumentORM) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            title=document.title,
            filename=document.filename,
            workspace_id=document.workspace_id,
            document_type=document.document_type,
            status=document.status,
            parser_version=document.parser_version,
            chunk_count=document.chunk_count,
            tags=document.tags or [],
            ingestion_options=document.ingestion_options or {},
            source_url=document.source_url,
            source_object_key=document.source_object_key,
            source_content_type=document.source_content_type,
            size_bytes=document.size_bytes,
            created_at=document.created_at,
            updated_at=document.updated_at,
            error_message=document.error_message,
        )

    @staticmethod
    def _to_job_schema(job: DocumentJobORM) -> DocumentJobResponse:
        return DocumentJobResponse(
            id=job.id,
            name=job.name,
            status=job.status,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
        )

    @staticmethod
    def _to_artifact_schema(artifact: DocumentArtifactORM) -> DocumentArtifactResponse:
        return DocumentArtifactResponse(
            id=artifact.id,
            document_id=artifact.document_id,
            workspace_id=artifact.workspace_id,
            artifact_type=artifact.artifact_type,
            name=artifact.name,
            object_key=artifact.object_key,
            public_url=artifact.public_url,
            content_type=artifact.content_type,
            size_bytes=artifact.size_bytes,
            metadata=artifact.metadata_json or {},
            created_at=artifact.created_at,
        )

    @staticmethod
    def _to_extraction_run_schema(run: DocumentExtractionRunORM) -> DocumentExtractionRunResponse:
        return DocumentExtractionRunResponse(
            id=run.id,
            document_id=run.document_id,
            workspace_id=run.workspace_id,
            status=run.status,
            schema_json=run.schema_json,
            result_json=run.result_json,
            parser_version=run.parser_version,
            use_llm=run.use_llm,
            error_message=run.error_message,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _job_sort_key(job: DocumentJobORM) -> int:
        if job.name in PIPELINE_JOB_NAMES:
            return PIPELINE_JOB_NAMES.index(job.name)
        return len(PIPELINE_JOB_NAMES)

    @staticmethod
    def _get_job(session, document_id: str, name: str) -> DocumentJobORM:
        job = session.scalar(
            select(DocumentJobORM).where(
                DocumentJobORM.document_id == document_id,
                DocumentJobORM.name == name,
            )
        )
        if job is None:
            raise DocumentProcessingError(f"Job '{name}' was not found for document '{document_id}'.")
        return job
