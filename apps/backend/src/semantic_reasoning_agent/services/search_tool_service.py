"""Service for `supersearch.docs` and `supersearch.graph` tool configs.

Responsibilities:
- CRUD for ``SearchToolConfigORM`` (workspace-scoped persistence of the
  one-time config the user selects in the UI).
- Readiness check against ``ModelConfigService`` so the UI can flag
  broken provider/model selections before a run.
- Execute a configured docs/graph search by resolving the config,
  running the appropriate pipeline (semantic + BM25 fusion for docs;
  Graphiti or published-ontology fallback for graph), and returning
  results in ``Evidence`` shape.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import select

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    DocumentChunkORM,
    OntologyEntityORM,
    OntologyRelationORM,
    OntologyVersionORM,
    SearchToolConfigORM,
)
from semantic_reasoning_agent.schemas.search_tools import (
    SearchToolConfigCreateRequest,
    SearchToolConfigResponse,
    SearchToolConfigUpdateRequest,
    SearchToolRunRequest,
    SearchToolRunResponse,
)
from semantic_reasoning_agent.schemas.tools import (
    CitationAnchorSchema,
    EvidenceSchema,
    ProvenanceSchema,
    ToolMetaSchema,
)
from semantic_reasoning_agent.services.bm25_scorer import BM25Scorer
from semantic_reasoning_agent.services.evidence_from_retrieval import retrieval_result_to_evidence
from semantic_reasoning_agent.services.hybrid_retrieval_service import reciprocal_rank_fuse
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.retrieval_service import RetrievalService, excerpt

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway


TOOL_NAME_DOCS = "supersearch.docs"
TOOL_NAME_GRAPH = "supersearch.graph"


class SearchToolConfigNotFoundError(LookupError):
    """Raised when a config id cannot be resolved for the current workspace."""


class SearchToolConfigInvalidError(ValueError):
    """Raised when a create/update payload fails cross-field validation."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SearchToolConfigService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_manager: DatabaseManager,
        model_config_service: ModelConfigService,
        retrieval_service: RetrievalService,
        graphiti_gateway: "GraphitiGateway | None" = None,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._model_config_service = model_config_service
        self._retrieval_service = retrieval_service
        self._graphiti_gateway = graphiti_gateway

    # ---------------- CRUD ----------------

    def create(self, payload: SearchToolConfigCreateRequest) -> SearchToolConfigResponse:
        workspace_id = payload.workspace_id or self._settings.default_workspace_id
        self._validate_payload_for_type(payload)
        config_id = str(uuid4())
        now = _utc_now()
        with self._database_manager.session() as session:
            existing = session.scalar(
                select(SearchToolConfigORM).where(
                    SearchToolConfigORM.workspace_id == workspace_id,
                    SearchToolConfigORM.tool_type == payload.tool_type,
                    SearchToolConfigORM.name == payload.name,
                )
            )
            if existing is not None:
                raise SearchToolConfigInvalidError(
                    f"Search tool config name '{payload.name}' already exists for this workspace."
                )
            orm = SearchToolConfigORM(
                id=config_id,
                workspace_id=workspace_id,
                tool_type=payload.tool_type,
                name=payload.name.strip(),
                description=payload.description or "",
                provider=payload.provider,
                model=payload.model,
                default_top_k=payload.default_top_k,
                collection_target=payload.collection_target,
                document_ids=list(payload.document_ids or []),
                bm25_enabled=bool(payload.bm25_enabled),
                fusion_strategy=payload.fusion_strategy,
                ontology_scope=payload.ontology_scope,
                ontology_version_id=payload.ontology_version_id,
                graph_search_type=payload.graph_search_type,
                reranker=payload.reranker,
                config_metadata=dict(payload.config_metadata or {}),
                created_at=now,
                updated_at=now,
            )
            session.add(orm)
            session.flush()
            return self._to_response(orm)

    def update(
        self,
        config_id: str,
        payload: SearchToolConfigUpdateRequest,
        *,
        workspace_id: str | None = None,
    ) -> SearchToolConfigResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            if payload.name is not None:
                new_name = payload.name.strip()
                if new_name != orm.name:
                    conflict = session.scalar(
                        select(SearchToolConfigORM).where(
                            SearchToolConfigORM.workspace_id == workspace_id,
                            SearchToolConfigORM.tool_type == orm.tool_type,
                            SearchToolConfigORM.name == new_name,
                            SearchToolConfigORM.id != config_id,
                        )
                    )
                    if conflict is not None:
                        raise SearchToolConfigInvalidError(
                            f"Search tool config name '{new_name}' already exists for this workspace."
                        )
                orm.name = new_name
            if payload.description is not None:
                orm.description = payload.description
            if payload.provider is not None:
                orm.provider = payload.provider
            if payload.model is not None:
                orm.model = payload.model
            if payload.default_top_k is not None:
                orm.default_top_k = payload.default_top_k
            if payload.collection_target is not None:
                orm.collection_target = payload.collection_target
            if payload.document_ids is not None:
                orm.document_ids = list(payload.document_ids)
            if payload.bm25_enabled is not None:
                orm.bm25_enabled = bool(payload.bm25_enabled)
            if payload.fusion_strategy is not None:
                orm.fusion_strategy = payload.fusion_strategy
            if payload.ontology_scope is not None:
                orm.ontology_scope = payload.ontology_scope
            if payload.ontology_version_id is not None:
                orm.ontology_version_id = payload.ontology_version_id or None
            if payload.graph_search_type is not None:
                orm.graph_search_type = payload.graph_search_type
            if payload.reranker is not None:
                orm.reranker = payload.reranker
            if payload.config_metadata is not None:
                orm.config_metadata = dict(payload.config_metadata)
            orm.updated_at = _utc_now()
            self._validate_orm(orm)
            session.flush()
            return self._to_response(orm)

    def delete(self, config_id: str, *, workspace_id: str | None = None) -> None:
        workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            session.delete(orm)

    def get(self, config_id: str, *, workspace_id: str | None = None) -> SearchToolConfigResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            return self._to_response(orm)

    def list(
        self,
        *,
        workspace_id: str | None = None,
        tool_type: str | None = None,
    ) -> list[SearchToolConfigResponse]:
        workspace_id = workspace_id or self._settings.default_workspace_id
        with self._database_manager.session() as session:
            statement = select(SearchToolConfigORM).where(
                SearchToolConfigORM.workspace_id == workspace_id
            )
            if tool_type:
                statement = statement.where(SearchToolConfigORM.tool_type == tool_type)
            statement = statement.order_by(
                SearchToolConfigORM.tool_type, SearchToolConfigORM.name
            )
            configs = session.scalars(statement).all()
            return [self._to_response(config) for config in configs]

    # ---------------- Execution ----------------

    def run(
        self,
        config_id: str,
        payload: SearchToolRunRequest,
        *,
        workspace_id: str | None = None,
    ) -> SearchToolRunResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        started = time.perf_counter()
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            tool_type = orm.tool_type
            config = self._to_response(orm)

        tool_name = TOOL_NAME_DOCS if tool_type == "docs" else TOOL_NAME_GRAPH
        call_id = uuid4()

        readiness_reason: str | None = None
        if not self._model_config_service.is_ready(
            config.provider, config.model, config.workspace_id
        ):
            readiness_reason = (
                f"Provider '{config.provider}' / model '{config.model}' is not ready. "
                "Configure it in workspace settings."
            )

        try:
            if tool_type == "docs":
                evidence = self._run_docs(config, payload, call_id)
            else:
                evidence = self._run_graph(config, payload, call_id)
        except Exception as exc:  # pragma: no cover - defensive guard
            return SearchToolRunResponse(
                config_id=config.id,
                tool_type=tool_type,
                tool_name=tool_name,
                status="failed",
                query=payload.query,
                error_code="supersearch_exception",
                error_message=str(exc),
                latency_ms=int((time.perf_counter() - started) * 1000),
                meta=ToolMetaSchema(
                    provider=config.provider,
                    trace_id=str(call_id),
                ),
            )

        latency_ms = int((time.perf_counter() - started) * 1000)
        next_hints: list[str] = []
        if readiness_reason:
            next_hints.append("provider_not_ready")
        if not evidence:
            next_hints.append("no_match")
        status = "success" if evidence else "partial"
        if readiness_reason and not evidence:
            status = "partial"

        return SearchToolRunResponse(
            config_id=config.id,
            tool_type=tool_type,
            tool_name=tool_name,
            status=status,
            query=payload.query,
            evidence=[self._evidence_to_schema(item) for item in evidence],
            next_action_hints=next_hints,
            error_code=None,
            error_message=readiness_reason,
            latency_ms=latency_ms,
            meta=ToolMetaSchema(
                provider=config.provider,
                provider_version=config.model,
                trace_id=str(call_id),
            ),
        )

    # ---------------- Docs pipeline ----------------

    def _run_docs(
        self,
        config: SearchToolConfigResponse,
        payload: SearchToolRunRequest,
        call_id: UUID,
    ) -> list[Evidence]:
        top_k = payload.top_k or config.default_top_k
        bm25_enabled = payload.bm25_enabled if payload.bm25_enabled is not None else config.bm25_enabled
        fusion = payload.fusion_strategy or config.fusion_strategy
        document_ids = list(config.document_ids) if config.collection_target == "documents" else None
        captured_at = _utc_now()

        semantic_evidence: list[Evidence] = []
        if fusion != "bm25_only":
            semantic_response = self._retrieval_service.search(
                query=payload.query,
                workspace_id=config.workspace_id,
                document_ids=document_ids,
                top_k=max(top_k * 2, top_k),
            )
            semantic_evidence = [
                retrieval_result_to_evidence(
                    result,
                    workspace_id=config.workspace_id,
                    tool_call_id=call_id,
                    captured_at=captured_at,
                )
                for result in semantic_response.results
            ]

        bm25_evidence: list[Evidence] = []
        if bm25_enabled and fusion != "semantic_only":
            bm25_evidence = self._bm25_evidence(
                config.workspace_id,
                payload.query,
                document_ids=document_ids,
                top_k=max(top_k * 2, top_k),
                call_id=call_id,
                captured_at=captured_at,
            )

        if fusion == "bm25_only":
            return bm25_evidence[:top_k]
        if fusion == "semantic_only" or not bm25_evidence:
            return semantic_evidence[:top_k]
        if not semantic_evidence:
            return bm25_evidence[:top_k]
        fused = reciprocal_rank_fuse([semantic_evidence, bm25_evidence], top_k=top_k)
        return fused

    def _bm25_evidence(
        self,
        workspace_id: str,
        query: str,
        *,
        document_ids: list[str] | None,
        top_k: int,
        call_id: UUID,
        captured_at: datetime,
    ) -> list[Evidence]:
        with self._database_manager.session() as session:
            statement = select(DocumentChunkORM).where(
                DocumentChunkORM.workspace_id == workspace_id
            )
            if document_ids:
                statement = statement.where(DocumentChunkORM.document_id.in_(document_ids))
            chunks = list(session.scalars(statement).all())
        if not chunks:
            return []
        corpus = [(chunk.chunk_id, chunk.text) for chunk in chunks]
        scorer = BM25Scorer(corpus)
        hits = scorer.score(query, top_k=top_k)
        chunk_lookup = {chunk.chunk_id: chunk for chunk in chunks}
        evidence: list[Evidence] = []
        for hit in hits:
            chunk = chunk_lookup.get(hit.chunk_id)
            if chunk is None:
                continue
            evidence.append(self._chunk_to_evidence(chunk, hit.score, call_id, captured_at))
        return evidence

    @staticmethod
    def _chunk_to_evidence(
        chunk: DocumentChunkORM,
        score: float,
        call_id: UUID,
        captured_at: datetime,
    ) -> Evidence:
        location_label = "document"
        if chunk.document_type == "pdf" and chunk.page_number is not None:
            location_label = f"page {chunk.page_number}"
        elif chunk.document_type == "docx" and chunk.heading_path:
            location_label = chunk.heading_path
        elif (
            chunk.document_type in {"xlsx", "csv"}
            and chunk.row_start is not None
            and chunk.row_end is not None
        ):
            prefix = f"{chunk.sheet_name} " if chunk.sheet_name else ""
            location_label = f"{prefix}rows {chunk.row_start}-{chunk.row_end}".strip()
        anchor_type = "page" if chunk.document_type == "pdf" and chunk.page_number else "section"
        locator = str(chunk.page_number) if chunk.document_type == "pdf" and chunk.page_number else (
            chunk.heading_path or location_label
        )
        return Evidence(
            evidence_id=uuid4(),
            source_type="internal_chunk",
            title=chunk.document_title,
            content=excerpt(chunk.text),
            citation_anchor=CitationAnchor(
                anchor_type=anchor_type,
                label=location_label,
                locator=locator,
            ),
            provenance=Provenance(
                workspace_id=chunk.workspace_id,
                source_id=chunk.document_id,
                tool_call_id=call_id,
                captured_at=captured_at,
            ),
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            page=chunk.page_number,
            section=chunk.heading_path,
            sheet_name=chunk.sheet_name,
            row_range=(
                f"{chunk.row_start}-{chunk.row_end}"
                if chunk.row_start is not None and chunk.row_end is not None
                else None
            ),
            score=float(score),
            uri=chunk.source_url or None,
        )

    # ---------------- Graph pipeline ----------------

    def _run_graph(
        self,
        config: SearchToolConfigResponse,
        payload: SearchToolRunRequest,
        call_id: UUID,
    ) -> list[Evidence]:
        top_k = payload.top_k or config.default_top_k
        reranker = payload.reranker or config.reranker

        if self._graphiti_gateway is not None and self._graphiti_gateway.is_enabled():
            from semantic_reasoning_agent.infrastructure.graphiti.graphiti_mapper import (
                map_edge_to_evidence,
                map_node_to_evidence,
            )

            matches = self._graphiti_gateway.search(
                query=payload.query,
                workspace_id=config.workspace_id,
                limit=top_k,
                search_type=config.graph_search_type,  # type: ignore[arg-type]
                reranker=reranker,  # type: ignore[arg-type]
            )
            evidence: list[Evidence] = []
            for match in matches:
                if match.kind == "edge":
                    evidence.append(
                        map_edge_to_evidence(
                            match.item,
                            workspace_id=config.workspace_id,
                            tool_call_id=call_id,
                            score=match.score,
                        )
                    )
                else:
                    evidence.append(
                        map_node_to_evidence(
                            match.item,
                            workspace_id=config.workspace_id,
                            tool_call_id=call_id,
                            score=match.score,
                        )
                    )
            if evidence:
                return evidence
            # Fall through to SQL fallback when Graphiti returns nothing.

        return self._run_graph_sql_fallback(config, payload, call_id, top_k)

    def _run_graph_sql_fallback(
        self,
        config: SearchToolConfigResponse,
        payload: SearchToolRunRequest,
        call_id: UUID,
        top_k: int,
    ) -> list[Evidence]:
        version_id = self._resolve_ontology_version_id(config)
        if version_id is None:
            return []
        query_lower = payload.query.lower()
        captured_at = _utc_now()
        with self._database_manager.session() as session:
            entities = session.scalars(
                select(OntologyEntityORM).where(
                    OntologyEntityORM.workspace_id == config.workspace_id,
                    OntologyEntityORM.version_id == version_id,
                )
            ).all()
            relations = session.scalars(
                select(OntologyRelationORM).where(
                    OntologyRelationORM.workspace_id == config.workspace_id,
                    OntologyRelationORM.version_id == version_id,
                )
            ).all()

        evidence: list[Evidence] = []
        search_type = config.graph_search_type
        if search_type in {"nodes", "combined"}:
            for entity in entities:
                score = _keyword_score(
                    query_lower,
                    [entity.name, entity.resolution_key, entity.entity_type],
                    aliases=entity.aliases or [],
                )
                if score <= 0:
                    continue
                evidence.append(_entity_to_evidence(entity, score, call_id, captured_at))
        if search_type in {"edges", "combined"}:
            for relation in relations:
                score = _keyword_score(
                    query_lower,
                    [relation.relation_type, relation.evidence_text],
                    aliases=[],
                )
                if score <= 0:
                    continue
                evidence.append(_relation_to_evidence(relation, score, call_id, captured_at))
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:top_k]

    def _resolve_ontology_version_id(self, config: SearchToolConfigResponse) -> str | None:
        if config.ontology_scope == "version" and config.ontology_version_id:
            return config.ontology_version_id
        with self._database_manager.session() as session:
            latest = session.scalar(
                select(OntologyVersionORM)
                .where(OntologyVersionORM.workspace_id == config.workspace_id)
                .order_by(OntologyVersionORM.version_number.desc())
            )
            return latest.id if latest else None

    # ---------------- Helpers ----------------

    def _validate_payload_for_type(self, payload: SearchToolConfigCreateRequest) -> None:
        if payload.tool_type == "docs":
            if payload.collection_target == "documents" and not payload.document_ids:
                raise SearchToolConfigInvalidError(
                    "collection_target='documents' requires at least one document_id."
                )
        elif payload.tool_type == "graph":
            if payload.ontology_scope == "version" and not payload.ontology_version_id:
                raise SearchToolConfigInvalidError(
                    "ontology_scope='version' requires ontology_version_id."
                )

    def _validate_orm(self, orm: SearchToolConfigORM) -> None:
        if orm.tool_type == "docs":
            if orm.collection_target == "documents" and not (orm.document_ids or []):
                raise SearchToolConfigInvalidError(
                    "collection_target='documents' requires at least one document_id."
                )
        elif orm.tool_type == "graph":
            if orm.ontology_scope == "version" and not orm.ontology_version_id:
                raise SearchToolConfigInvalidError(
                    "ontology_scope='version' requires ontology_version_id."
                )

    def _require_orm(
        self,
        session,  # noqa: ANN001
        config_id: str,
        workspace_id: str,
    ) -> SearchToolConfigORM:
        orm = session.scalar(
            select(SearchToolConfigORM).where(
                SearchToolConfigORM.id == config_id,
                SearchToolConfigORM.workspace_id == workspace_id,
            )
        )
        if orm is None:
            raise SearchToolConfigNotFoundError(
                f"Search tool config '{config_id}' not found in workspace '{workspace_id}'."
            )
        return orm

    def _to_response(self, orm: SearchToolConfigORM) -> SearchToolConfigResponse:
        ready = self._model_config_service.is_ready(
            orm.provider, orm.model, orm.workspace_id
        )
        reason = (
            "Ready to run."
            if ready
            else f"Provider '{orm.provider}' / model '{orm.model}' is not ready."
        )
        return SearchToolConfigResponse(
            id=orm.id,
            workspace_id=orm.workspace_id,
            tool_type=orm.tool_type,  # type: ignore[arg-type]
            name=orm.name,
            description=orm.description or "",
            provider=orm.provider,
            model=orm.model,
            default_top_k=orm.default_top_k,
            collection_target=orm.collection_target,  # type: ignore[arg-type]
            document_ids=list(orm.document_ids or []),
            bm25_enabled=bool(orm.bm25_enabled),
            fusion_strategy=orm.fusion_strategy,  # type: ignore[arg-type]
            ontology_scope=orm.ontology_scope,  # type: ignore[arg-type]
            ontology_version_id=orm.ontology_version_id,
            graph_search_type=orm.graph_search_type,  # type: ignore[arg-type]
            reranker=orm.reranker,  # type: ignore[arg-type]
            config_metadata=dict(orm.config_metadata or {}),
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            ready=ready,
            ready_reason=reason,
        )

    @staticmethod
    def _evidence_to_schema(evidence: Evidence) -> EvidenceSchema:
        return EvidenceSchema(
            evidence_id=evidence.evidence_id,
            source_type=evidence.source_type,
            title=evidence.title,
            content=evidence.content,
            citation_anchor=CitationAnchorSchema(
                anchor_type=evidence.citation_anchor.anchor_type,
                label=evidence.citation_anchor.label,
                locator=evidence.citation_anchor.locator,
            ),
            provenance=ProvenanceSchema(
                workspace_id=evidence.provenance.workspace_id,
                captured_at=evidence.provenance.captured_at,
                source_id=evidence.provenance.source_id,
                tool_call_id=evidence.provenance.tool_call_id,
                parser_version=evidence.provenance.parser_version,
                extractor_version=evidence.provenance.extractor_version,
                model=evidence.provenance.model,
            ),
            summary=evidence.summary,
            uri=evidence.uri,
            document_id=evidence.document_id,
            chunk_id=evidence.chunk_id,
            page=evidence.page,
            section=evidence.section,
            sheet_name=evidence.sheet_name,
            row_range=evidence.row_range,
            entity_ids=list(evidence.entity_ids),
            relation_ids=list(evidence.relation_ids),
            score=evidence.score,
            trust_score=evidence.trust_score,
            freshness_ts=evidence.freshness_ts,
        )


def _keyword_score(query_lower: str, fields: list[str | None], *, aliases: list[str]) -> float:
    if not query_lower:
        return 0.0
    tokens = [token for token in query_lower.split() if token]
    if not tokens:
        return 0.0
    haystack = " ".join((value or "").lower() for value in fields)
    alias_text = " ".join((alias or "").lower() for alias in aliases)
    full = f"{haystack} {alias_text}".strip()
    if not full:
        return 0.0
    score = 0.0
    for token in tokens:
        if not token:
            continue
        if token in full:
            score += 1.0
    return score


def _entity_to_evidence(
    entity: OntologyEntityORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_node",
        title=entity.name,
        content=f"{entity.name} ({entity.entity_type})",
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=entity.entity_type,
            locator=f"ontology-entity:{entity.id}",
        ),
        provenance=Provenance(
            workspace_id=entity.workspace_id,
            source_id=entity.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        entity_ids=(entity.id,),
        score=float(score),
    )


def _relation_to_evidence(
    relation: OntologyRelationORM,
    score: float,
    call_id: UUID,
    captured_at: datetime,
) -> Evidence:
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_edge",
        title=relation.relation_type,
        content=relation.evidence_text,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=relation.relation_type,
            locator=f"ontology-relation:{relation.id}",
        ),
        provenance=Provenance(
            workspace_id=relation.workspace_id,
            source_id=relation.id,
            tool_call_id=call_id,
            captured_at=captured_at,
        ),
        relation_ids=(relation.id,),
        entity_ids=(relation.source_entity_id, relation.target_entity_id),
        score=float(score),
    )


__all__ = [
    "SearchToolConfigService",
    "SearchToolConfigNotFoundError",
    "SearchToolConfigInvalidError",
    "TOOL_NAME_DOCS",
    "TOOL_NAME_GRAPH",
]
