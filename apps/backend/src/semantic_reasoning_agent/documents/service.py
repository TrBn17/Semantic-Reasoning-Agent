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
from semantic_reasoning_agent.documents.chunking import MarkdownChunker
from semantic_reasoning_agent.documents.converters import MarkdownConverterService
from semantic_reasoning_agent.documents.models import (
    ConvertedDocument,
    DocumentIngestionMode,
    DocumentIngestionOptions,
)
from semantic_reasoning_agent.domain.contracts.llm import LLMMessage
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
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
from semantic_reasoning_agent.ports.task_model_resolver import TaskModelResolverPort
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


BASE_JOB_NAMES = ("convert_markdown", "store_artifacts")
RETRIEVAL_JOB_NAMES = ("build_chunks", "index_chunks")


def _pipeline_job_names(ingestion_mode: DocumentIngestionMode) -> tuple[str, ...]:
    if ingestion_mode in {"retrieval", "both"}:
        return BASE_JOB_NAMES + RETRIEVAL_JOB_NAMES
    return BASE_JOB_NAMES


class DocumentService:
    """Orchestrates upload, markdown conversion, artifacts, and retrieval indexing."""

    def __init__(
        self,
        settings: Settings,
        markdown_converter: MarkdownConverterService,
        markdown_chunker: MarkdownChunker,
        retrieval_service: RetrievalService,
        database_manager: DatabaseManager,
        task_dispatcher: TaskDispatcher,
        object_store: ObjectStorePort | None = None,
        model_config_service: TaskModelResolverPort | None = None,
        adapter_registry: AdapterRegistry | None = None,
    ) -> None:
        self._settings = settings
        self._markdown_converter = markdown_converter
        self._markdown_chunker = markdown_chunker
        self._retrieval_service = retrieval_service
        self._database_manager = database_manager
        self._task_dispatcher = task_dispatcher
        self._object_store = object_store or build_object_store(settings)
        self._model_config_service = model_config_service
        self._adapter_registry = adapter_registry

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
        supported_types = sorted(self._markdown_converter.supported_types())
        return DocumentIngestionCapabilitiesResponse(
            supported_types=supported_types,
            default_options=DocumentIngestionOptionsResponse(
                ingestion_mode="both",
            ),
            ingestion_mode_options=[
                DocumentOptionChoice(
                    value="ontology",
                    label="Ontology only",
                    description="Convert to markdown and keep ontology pipeline independent from retrieval.",
                ),
                DocumentOptionChoice(
                    value="retrieval",
                    label="Retrieval only",
                    description="Convert to markdown, chunk and embed into vector storage.",
                ),
                DocumentOptionChoice(
                    value="both",
                    label="Both",
                    description="Run ontology-ready markdown and retrieval chunk/index in parallel.",
                ),
            ],
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
        ingestion_mode: str | None = None,
        content_type: str | None = None,
    ) -> DocumentResponse:
        if not content:
            raise DocumentProcessingError("Uploaded file is empty.")
        if not self._markdown_converter.supports(filename):
            raise UnsupportedDocumentTypeError(
                f"Unsupported document type '{Path(filename).suffix.lower().lstrip('.')}'. "
                + "Supported types: "
                + ", ".join(self._markdown_converter.supported_types())
                + "."
            )

        document_type = Path(filename).suffix.lower().lstrip(".")
        ingestion_options = self._resolve_ingestion_options(ingestion_mode=ingestion_mode)
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
            ingestion_mode=ingestion_options.ingestion_mode,
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
            session.add_all(
                self._build_job_records(document_id, ingestion_mode=ingestion_options.ingestion_mode)
            )

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
        markdown = self._latest_artifact_text(document.id, "markdown")
        if not markdown:
            raise DocumentProcessingError(
                "Structured extraction requires a markdown artifact. Reprocess the document first."
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
            result_json = self._extract_json_from_markdown(
                markdown=markdown,
                schema_json=payload.extraction_schema,
                use_llm=payload.use_llm,
                workspace_id=document.workspace_id,
            )
            self._update_extraction_run(
                run_id,
                status="completed",
                result_json=result_json,
                parser_version=document.parser_version,
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
        options = DocumentIngestionOptions.from_dict(document.ingestion_options)
        self._reset_jobs(document_id, ingestion_mode=options.ingestion_mode)
        self._retrieval_service.remove_document(document_id)

        try:
            self._mark_job_running(document_id, "convert_markdown")
            binary_content = self._object_store.get_document_binary(
                document.id,
                document.source_object_key,
                fallback_content=document.binary_content,
            )
            converted_document = self._markdown_converter.convert(
                document.filename,
                binary_content,
                title=document.title,
                content_type=document.source_content_type,
            )
            self._mark_job_completed(document_id, "convert_markdown")
            self._update_document_state(
                document_id,
                status=DocumentStatus.parsed.value,
                parser_version=converted_document.converter_version,
                error_message=None,
            )

            self._mark_job_running(document_id, "store_artifacts")
            self._replace_artifacts(document, converted_document)
            self._mark_job_completed(document_id, "store_artifacts")

            chunk_count = 0
            if options.ingestion_mode in {"retrieval", "both"}:
                self._mark_job_running(document_id, "build_chunks")
                parsed_chunks = self._markdown_chunker.split(converted_document.markdown)
                chunk_count = len(parsed_chunks)
                self._mark_job_completed(document_id, "build_chunks")

                self._mark_job_running(document_id, "index_chunks")
                document_schema = self._to_document_schema(document)
                indexed_chunks = self._retrieval_service.prepare_chunks(
                    document_schema,
                    parsed_chunks,
                    parser_version=converted_document.converter_version,
                )
                self._retrieval_service.upsert_chunks(document_id, indexed_chunks)
                self._mark_job_completed(document_id, "index_chunks")

            self._update_document_state(
                document_id,
                status=DocumentStatus.indexed.value,
                parser_version=converted_document.converter_version,
                chunk_count=chunk_count,
                error_message=None,
            )
        except UnsupportedDocumentTypeError as exc:
            self._mark_failed(document_id, self._active_job_name(document_id), str(exc))
            raise
        except Exception as exc:
            self._mark_failed(document_id, self._active_job_name(document_id), str(exc))
            raise DocumentProcessingError(str(exc)) from exc

    def _resolve_ingestion_options(self, *, ingestion_mode: str | None) -> DocumentIngestionOptions:
        mode = str(ingestion_mode or "both").lower()
        if mode not in {"ontology", "retrieval", "both"}:
            raise DocumentProcessingError(
                "ingestion_mode must be one of 'ontology', 'retrieval', or 'both'."
            )
        return DocumentIngestionOptions(ingestion_mode=mode)  # type: ignore[arg-type]

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
                ingestion_mode=document.ingestion_mode,
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
            options = DocumentIngestionOptions.from_dict(row.ingestion_options)
            row.status = DocumentStatus.uploaded.value
            row.error_message = None
            row.chunk_count = 0
            row.updated_at = utc_now()
            session.execute(delete(DocumentChunkORM).where(DocumentChunkORM.document_id == document_id))
            session.execute(delete(DocumentJobORM).where(DocumentJobORM.document_id == document_id))
            session.execute(delete(DocumentArtifactORM).where(DocumentArtifactORM.document_id == document_id))
            session.execute(delete(DocumentExtractionRunORM).where(DocumentExtractionRunORM.document_id == document_id))
            session.add_all(
                self._build_job_records(document_id, ingestion_mode=options.ingestion_mode)
            )

    def _queue_document(self, document_id: str) -> None:
        try:
            self._task_dispatcher.enqueue_document_processing(document_id)
        except Exception as exc:
            raise DocumentProcessingError(f"Failed to queue document '{document_id}' for ingestion.") from exc

    def _reset_jobs(self, document_id: str, *, ingestion_mode: DocumentIngestionMode) -> None:
        with self._database_manager.session() as session:
            jobs = session.scalars(select(DocumentJobORM).where(DocumentJobORM.document_id == document_id)).all()
            if not jobs:
                session.add_all(self._build_job_records(document_id, ingestion_mode=ingestion_mode))
                return
            active_jobs = set(_pipeline_job_names(ingestion_mode))
            for job in jobs:
                if job.name not in active_jobs:
                    session.delete(job)
                    continue
                job.status = JobStatus.pending.value
                job.started_at = None
                job.finished_at = None
                job.error_message = None
            for name in active_jobs:
                if not any(job.name == name for job in jobs):
                    session.add(
                        DocumentJobORM(
                            id=f"{document_id}:{name}",
                            document_id=document_id,
                            name=name,
                            status=JobStatus.pending.value,
                            started_at=None,
                            finished_at=None,
                            error_message=None,
                        )
                    )

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

    def _replace_artifacts(self, document: DocumentORM, converted_document: ConvertedDocument) -> None:
        with self._database_manager.session() as session:
            session.execute(delete(DocumentArtifactORM).where(DocumentArtifactORM.document_id == document.id))
        markdown = converted_document.markdown.strip()
        if markdown:
            self._store_artifact(
                document_id=document.id,
                workspace_id=document.workspace_id,
                artifact_type="markdown",
                artifact_name="document.md",
                content=markdown.encode("utf-8"),
                content_type="text/markdown",
                metadata={"inline_text": markdown},
            )
        self._store_artifact(
            document_id=document.id,
            workspace_id=document.workspace_id,
            artifact_type="normalized_json",
            artifact_name="document.json",
            content=json.dumps(
                {
                    "document_type": converted_document.document_type,
                    "converter_name": converted_document.converter_name,
                    "converter_version": converted_document.converter_version,
                    "metadata": converted_document.metadata,
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            content_type="application/json",
            metadata={},
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
        if content:
            return content.decode("utf-8")
        inline_text = (artifact.metadata_json or {}).get("inline_text")
        if isinstance(inline_text, str):
            return inline_text
        return None

    def _extract_json_from_markdown(
        self,
        *,
        markdown: str,
        schema_json: dict[str, object],
        use_llm: bool,
        workspace_id: str,
    ) -> dict[str, object]:
        text = markdown.strip()
        if not text:
            return {"schema": schema_json, "items": []}

        if use_llm:
            payload = self._extract_json_with_llm(
                markdown=text,
                schema_json=schema_json,
                workspace_id=workspace_id,
            )
            if payload is not None:
                return payload

        lines = [line.strip("-* \t") for line in text.splitlines() if line.strip()]
        return {
            "schema": schema_json,
            "items": lines[:20],
            "source": "heuristic",
        }

    def _extract_json_with_llm(
        self,
        *,
        markdown: str,
        schema_json: dict[str, object],
        workspace_id: str,
    ) -> dict[str, object] | None:
        if self._model_config_service is None or self._adapter_registry is None:
            return None
        provider = self._settings.ontology_llm_provider
        model = self._settings.ontology_llm_model
        if not provider or not model:
            return None
        if not self._model_config_service.is_ready(provider, model, workspace_id):
            return None
        adapter = self._adapter_registry.get(provider)
        if adapter is None:
            return None

        prompt = (
            "Extract structured JSON from markdown.\n"
            "Return strict JSON object with keys: schema, result.\n"
            f"Target schema:\n{json.dumps(schema_json, ensure_ascii=False)}\n\n"
            f"Markdown:\n{markdown[:50000]}"
        )
        response = adapter.run(
            messages=[LLMMessage(role="user", content=prompt)],
            tools=(),
            tool_choice="none",
            max_tokens=2000,
            temperature=0,
            model=model,
        )
        content = (response.content or "").strip()
        if not content:
            return None
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return payload

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
        document = self._get_document_record(document_id)
        ingestion_mode = DocumentIngestionOptions.from_dict(document.ingestion_options).ingestion_mode
        job_order = _pipeline_job_names(ingestion_mode)
        with self._database_manager.session() as session:
            jobs = session.scalars(select(DocumentJobORM).where(DocumentJobORM.document_id == document_id)).all()
            for name in reversed(job_order):
                for job in jobs:
                    if job.name == name and job.status == JobStatus.running.value:
                        return name
        return job_order[0]

    @staticmethod
    def _build_job_records(
        document_id: str,
        *,
        ingestion_mode: DocumentIngestionMode,
    ) -> list[DocumentJobORM]:
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
            for name in _pipeline_job_names(ingestion_mode)
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
        document = session.get(DocumentORM, document_id)
        ingestion_mode = DocumentIngestionOptions.from_dict(
            document.ingestion_options if document else {}
        ).ingestion_mode
        for name in _pipeline_job_names(ingestion_mode):
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
            ingestion_mode=document.ingestion_mode,
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
        ordered_jobs = list(BASE_JOB_NAMES) + list(RETRIEVAL_JOB_NAMES)
        if job.name in ordered_jobs:
            return ordered_jobs.index(job.name)
        return len(ordered_jobs)

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
