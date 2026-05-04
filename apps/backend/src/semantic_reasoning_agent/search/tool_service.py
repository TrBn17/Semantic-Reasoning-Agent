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
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import (
    OntologySearchIndexORM,
    OntologyEntityFactORM,
    OntologyEntityORM,
    OntologyEntityTypeDefinitionORM,
    OntologyRelationFactORM,
    OntologyRelationORM,
    OntologyRelationTypeDefinitionORM,
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
from semantic_reasoning_agent.retrieval.ranking import reciprocal_rank_fuse
from semantic_reasoning_agent.services.model_config_service import ModelConfigService
from semantic_reasoning_agent.services.ontology_graph_projection_service import (
    OntologyGraphProjectionError,
)
from semantic_reasoning_agent.services.retrieval_service import RetrievalService, excerpt

from semantic_reasoning_agent.search.constants import (
    DEFAULT_DOCS_SYSTEM_KEY,
    DEFAULT_GRAPH_SYSTEM_KEY,
    FORCED_EMBEDDING_MODEL,
    FORCED_EMBEDDING_PROVIDER,
    TOOL_NAME_DOCS,
    TOOL_NAME_GRAPH,
    RouteDecision,
    SearchToolConfigInvalidError,
    SearchToolConfigNotFoundError,
    SearchToolSystemManagedError,
    _utc_now,
)
from semantic_reasoning_agent.search.sql_evidence import (
    _entity_fact_to_evidence,
    _entity_to_evidence,
    _keyword_score,
    _relation_fact_to_evidence,
    _relation_to_evidence,
)

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
    from semantic_reasoning_agent.services.ontology_graph_projection_service import (
        OntologyGraphProjectionService,
    )


class SearchToolConfigService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_manager: DatabaseManager,
        model_config_service: ModelConfigService,
        retrieval_service: RetrievalService,
        graphiti_gateway: "GraphitiGateway | None" = None,
        ontology_graph_projection_service: "OntologyGraphProjectionService | None" = None,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._model_config_service = model_config_service
        self._retrieval_service = retrieval_service
        self._graphiti_gateway = graphiti_gateway
        self._ontology_graph_projection_service = ontology_graph_projection_service

    # ---------------- CRUD ----------------

    def create(self, payload: SearchToolConfigCreateRequest) -> SearchToolConfigResponse:
        workspace_id = payload.workspace_id or self._settings.default_workspace_id
        self.ensure_workspace_defaults(workspace_id)
        self._validate_payload_for_type(payload)
        embedding_provider, embedding_model = self._resolve_embedding_fields(
            workspace_id,
            embedding_provider=payload.embedding_provider or payload.provider,
            embedding_model=payload.embedding_model or payload.model,
        )
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
                provider=payload.provider or embedding_provider,
                model=payload.model or embedding_model,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                default_top_k=payload.default_top_k,
                system_key=None,
                is_system=False,
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
        self.ensure_workspace_defaults(workspace_id)
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            if orm.is_system:
                raise SearchToolSystemManagedError(
                    f"Search tool config '{orm.name}' is system-managed. Duplicate it to customize."
                )
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
            if payload.embedding_provider is not None or payload.embedding_model is not None:
                embedding_provider, embedding_model = self._resolve_embedding_fields(
                    workspace_id,
                    embedding_provider=payload.embedding_provider or orm.embedding_provider,
                    embedding_model=payload.embedding_model or orm.embedding_model,
                )
                orm.embedding_provider = embedding_provider
                orm.embedding_model = embedding_model
                if payload.provider is None:
                    orm.provider = embedding_provider
                if payload.model is None:
                    orm.model = embedding_model
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

    def duplicate(
        self,
        config_id: str,
        *,
        workspace_id: str | None = None,
    ) -> SearchToolConfigResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        self.ensure_workspace_defaults(workspace_id)
        now = _utc_now()
        with self._database_manager.session() as session:
            source = self._require_orm(session, config_id, workspace_id)
            duplicate_name = self._next_duplicate_name(
                session,
                workspace_id=workspace_id,
                tool_type=source.tool_type,
                base_name=source.name,
            )
            duplicated = SearchToolConfigORM(
                id=str(uuid4()),
                workspace_id=workspace_id,
                tool_type=source.tool_type,
                name=duplicate_name,
                description=source.description or "",
                system_key=None,
                is_system=False,
                provider=source.provider,
                model=source.model,
                embedding_provider=source.embedding_provider,
                embedding_model=source.embedding_model,
                default_top_k=source.default_top_k,
                collection_target=source.collection_target,
                document_ids=list(source.document_ids or []),
                bm25_enabled=bool(source.bm25_enabled),
                fusion_strategy=source.fusion_strategy,
                ontology_scope=source.ontology_scope,
                ontology_version_id=source.ontology_version_id,
                graph_search_type=source.graph_search_type,
                reranker=source.reranker,
                config_metadata=dict(source.config_metadata or {}),
                created_at=now,
                updated_at=now,
            )
            session.add(duplicated)
            session.flush()
            return self._to_response(duplicated)

    def delete(self, config_id: str, *, workspace_id: str | None = None) -> None:
        workspace_id = workspace_id or self._settings.default_workspace_id
        self.ensure_workspace_defaults(workspace_id)
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            if orm.is_system:
                raise SearchToolSystemManagedError(
                    f"Search tool config '{orm.name}' is system-managed and cannot be deleted."
                )
            session.delete(orm)

    def get(self, config_id: str, *, workspace_id: str | None = None) -> SearchToolConfigResponse:
        workspace_id = workspace_id or self._settings.default_workspace_id
        self.ensure_workspace_defaults(workspace_id)
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
        self.ensure_workspace_defaults(workspace_id)
        with self._database_manager.session() as session:
            statement = select(SearchToolConfigORM).where(
                SearchToolConfigORM.workspace_id == workspace_id
            )
            if tool_type:
                statement = statement.where(SearchToolConfigORM.tool_type == tool_type)
            statement = statement.order_by(
                SearchToolConfigORM.is_system.desc(),
                SearchToolConfigORM.tool_type,
                SearchToolConfigORM.name,
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
        self.ensure_workspace_defaults(workspace_id)
        started = time.perf_counter()
        with self._database_manager.session() as session:
            orm = self._require_orm(session, config_id, workspace_id)
            tool_type = orm.tool_type
            config = self._to_response(orm)

        tool_name = TOOL_NAME_DOCS if tool_type == "docs" else TOOL_NAME_GRAPH
        call_id = uuid4()

        readiness_reason: str | None = None
        ready, ready_reason = self._model_config_service.embedding_backend_status(
            config.embedding_provider,
            config.embedding_model,
            config.workspace_id,
        )
        if not ready:
            readiness_reason = ready_reason

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
                provider=config.embedding_provider,
                provider_version=config.embedding_model,
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
        document_ids = (
            list(payload.document_ids)
            if payload.document_ids is not None
            else list(config.document_ids) if config.collection_target == "documents" else None
        )
        knowledge_pack_ids = self._resolve_knowledge_pack_ids(config)
        captured_at = _utc_now()

        semantic_evidence: list[Evidence] = []
        if fusion != "bm25_only":
            semantic_response = self._retrieval_service.search(
                query=payload.query,
                workspace_id=config.workspace_id,
                document_ids=document_ids,
                top_k=max(top_k * 2, top_k),
                embedding_provider=config.embedding_provider,
                embedding_model=config.embedding_model,
                knowledge_pack_ids=knowledge_pack_ids,
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
                knowledge_pack_ids=knowledge_pack_ids,
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
        knowledge_pack_ids: list[str] | None,
        top_k: int,
        call_id: UUID,
        captured_at: datetime,
    ) -> list[Evidence]:
        chunks = self._retrieval_service.list_chunks_for_bm25(
            workspace_id=workspace_id,
            knowledge_pack_ids=knowledge_pack_ids,
            document_ids=document_ids,
        )
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
        chunk,
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
        route = self._decide_graph_route(config, payload.query)
        semantic_evidence = self._run_graph_semantic_index(config, payload, call_id, top_k)
        if semantic_evidence and route == "graph":
            return semantic_evidence

        if route == "sql_facts":
            return self._run_graph_facts_sql(config, payload, call_id, top_k)

        graph_evidence: list[Evidence] = []

        if self._graphiti_gateway is not None and self._graphiti_gateway.is_enabled():
            matches = self._graphiti_gateway.search(
                query=payload.query,
                group_ids=self._graphiti_group_ids_for_config(config),
                limit=top_k,
                search_type=config.graph_search_type,  # type: ignore[arg-type]
                reranker=reranker,  # type: ignore[arg-type]
            )
            from semantic_reasoning_agent.infrastructure.graphiti.graphiti_evidence import (
                graphiti_matches_to_evidence,
            )

            graph_evidence = graphiti_matches_to_evidence(
                matches,
                workspace_id=config.workspace_id,
                tool_call_id=call_id,
            )
            if graph_evidence and route == "graph":
                return graph_evidence
            # Fall through to SQL fallback when Graphiti returns nothing.
        if not graph_evidence:
            graph_evidence = self._run_graph_sql_fallback(config, payload, call_id, top_k)
            if route == "graph":
                return graph_evidence

        facts_evidence = self._run_graph_facts_sql(config, payload, call_id, top_k)
        merged = semantic_evidence + graph_evidence + facts_evidence if route == "hybrid" else semantic_evidence + graph_evidence
        merged.sort(key=lambda item: item.score, reverse=True)
        return merged[:top_k]

    def _run_graph_facts_sql(
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
            entity_facts = session.scalars(
                select(OntologyEntityFactORM).where(
                    OntologyEntityFactORM.workspace_id == config.workspace_id,
                    OntologyEntityFactORM.version_id == version_id,
                )
            ).all()
            relation_facts = session.scalars(
                select(OntologyRelationFactORM).where(
                    OntologyRelationFactORM.workspace_id == config.workspace_id,
                    OntologyRelationFactORM.version_id == version_id,
                )
            ).all()
        evidence: list[Evidence] = []
        for fact in entity_facts:
            score = _keyword_score(
                query_lower,
                [fact.metric_key, fact.value_text, fact.unit, str(fact.value_num) if fact.value_num is not None else None],
                aliases=[],
            )
            if score <= 0:
                continue
            evidence.append(_entity_fact_to_evidence(fact, score, call_id, captured_at))
        for fact in relation_facts:
            score = _keyword_score(
                query_lower,
                [fact.metric_key, fact.value_text, fact.unit, str(fact.value_num) if fact.value_num is not None else None],
                aliases=[],
            )
            if score <= 0:
                continue
            evidence.append(_relation_fact_to_evidence(fact, score, call_id, captured_at))
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:top_k]

    def _decide_graph_route(self, config: SearchToolConfigResponse, query: str) -> RouteDecision:
        query_lower = query.lower()
        version_id = self._resolve_ontology_version_id(config)
        if version_id is None:
            return "graph"

        rules: list[dict] = []
        config_rules = (config.config_metadata or {}).get("query_rules", [])
        if isinstance(config_rules, list):
            rules.extend([item for item in config_rules if isinstance(item, dict)])
        with self._database_manager.session() as session:
            entity_types = session.scalars(
                select(OntologyEntityTypeDefinitionORM).where(
                    OntologyEntityTypeDefinitionORM.workspace_id == config.workspace_id,
                    OntologyEntityTypeDefinitionORM.version_id == version_id,
                )
            ).all()
            relation_types = session.scalars(
                select(OntologyRelationTypeDefinitionORM).where(
                    OntologyRelationTypeDefinitionORM.workspace_id == config.workspace_id,
                    OntologyRelationTypeDefinitionORM.version_id == version_id,
                )
            ).all()
        for item in entity_types:
            rules.extend([rule for rule in (item.query_rules or []) if isinstance(rule, dict)])
        for item in relation_types:
            rules.extend([rule for rule in (item.query_rules or []) if isinstance(rule, dict)])
        if not rules:
            return "graph"

        route_scores: dict[RouteDecision, float] = defaultdict(float)
        for rule in rules:
            route_raw = str(rule.get("query_route") or "").strip().lower()
            route: RouteDecision
            if route_raw == "sql_facts":
                route = "sql_facts"
            elif route_raw == "hybrid":
                route = "hybrid"
            elif route_raw == "graph":
                route = "graph"
            else:
                continue
            triggers = [str(item).lower() for item in rule.get("trigger_keywords", []) if str(item).strip()]
            intents = [str(item).lower() for item in rule.get("intent_tags", []) if str(item).strip()]
            score = _keyword_score(query_lower, triggers + intents, aliases=[])
            if score <= 0:
                continue
            route_scores[route] += score
        if not route_scores:
            return "graph"
        return max(route_scores.items(), key=lambda item: item[1])[0]

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

    def _run_graph_semantic_index(
        self,
        config: SearchToolConfigResponse,
        payload: SearchToolRunRequest,
        call_id: UUID,
        top_k: int,
    ) -> list[Evidence]:
        version_id = self._resolve_ontology_version_id(config)
        if version_id is None:
            return []
        self._ensure_ontology_index(
            workspace_id=config.workspace_id,
            version_id=version_id,
            embedding_provider=config.embedding_provider,
            embedding_model=config.embedding_model,
        )
        query_embedding = self._retrieval_service._embed_text(  # noqa: SLF001
            payload.query,
            workspace_id=config.workspace_id,
            provider=config.embedding_provider,
            model=config.embedding_model,
        )
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(OntologySearchIndexORM).where(
                    OntologySearchIndexORM.workspace_id == config.workspace_id,
                    OntologySearchIndexORM.version_id == version_id,
                    OntologySearchIndexORM.embedding_provider == config.embedding_provider,
                    OntologySearchIndexORM.embedding_model == config.embedding_model,
                )
            ).all()
        captured_at = _utc_now()
        evidence: list[Evidence] = []
        for row in rows:
            score = self._retrieval_service._cosine_similarity(query_embedding.values, row.embedding)  # noqa: SLF001
            if score <= 0:
                continue
            evidence.append(
                Evidence(
                    evidence_id=uuid4(),
                    source_type="graph_edge" if row.item_type.startswith("relation") else "graph_node",
                    title=row.title,
                    content=excerpt(row.content),
                    citation_anchor=CitationAnchor(
                        anchor_type="graph_ref",
                        label=row.item_type,
                        locator=f"{row.item_type}:{row.item_id}",
                    ),
                    provenance=Provenance(
                        workspace_id=row.workspace_id,
                        source_id=row.item_id,
                        tool_call_id=call_id,
                        captured_at=captured_at,
                        model=config.embedding_model,
                    ),
                    entity_ids=(row.item_id,) if row.item_type.startswith("entity") else (),
                    relation_ids=(row.item_id,) if row.item_type.startswith("relation") else (),
                    score=float(score),
                )
            )
        evidence.sort(key=lambda item: item.score, reverse=True)
        return evidence[:top_k]

    def ensure_workspace_defaults(self, workspace_id: str) -> None:
        now = _utc_now()
        with self._database_manager.session() as session:
            self._upsert_system_config(
                session,
                workspace_id=workspace_id,
                tool_type="docs",
                system_key=DEFAULT_DOCS_SYSTEM_KEY,
                name="Workspace RAG",
                description="System-managed default RAG tool for workspace documents.",
                embedding_provider=FORCED_EMBEDDING_PROVIDER,
                embedding_model=FORCED_EMBEDDING_MODEL,
                default_top_k=5,
                collection_target="workspace",
                bm25_enabled=True,
                fusion_strategy="hybrid_rrf",
                created_at=now,
            )
            graph_config = self._upsert_system_config(
                session,
                workspace_id=workspace_id,
                tool_type="graph",
                system_key=DEFAULT_GRAPH_SYSTEM_KEY,
                name="Workspace Ontology Search",
                description="System-managed default ontology search tool for the published graph.",
                embedding_provider=FORCED_EMBEDDING_PROVIDER,
                embedding_model=FORCED_EMBEDDING_MODEL,
                default_top_k=5,
                ontology_scope="published",
                graph_search_type="combined",
                reranker="rrf",
                created_at=now,
            )
            version_id = graph_config.ontology_version_id
        if version_id:
            self._ensure_ontology_index(
                workspace_id=workspace_id,
                version_id=version_id,
                embedding_provider=FORCED_EMBEDDING_PROVIDER,
                embedding_model=FORCED_EMBEDDING_MODEL,
            )

    def resolve_default_docs_config_id(self, workspace_id: str) -> str:
        """System default RAG ``SearchToolConfig`` id for workspace."""

        self.ensure_workspace_defaults(workspace_id)
        with self._database_manager.session() as session:
            orm = session.scalar(
                select(SearchToolConfigORM).where(
                    SearchToolConfigORM.workspace_id == workspace_id,
                    SearchToolConfigORM.system_key == DEFAULT_DOCS_SYSTEM_KEY,
                )
            )
        if orm is None:
            raise SearchToolConfigNotFoundError(
                f"Default docs search config missing for workspace '{workspace_id}'."
            )
        return str(orm.id)

    def resolve_default_graph_config_id(self, workspace_id: str) -> str:
        """System default ontology graph ``SearchToolConfig`` id."""

        self.ensure_workspace_defaults(workspace_id)
        with self._database_manager.session() as session:
            orm = session.scalar(
                select(SearchToolConfigORM).where(
                    SearchToolConfigORM.workspace_id == workspace_id,
                    SearchToolConfigORM.system_key == DEFAULT_GRAPH_SYSTEM_KEY,
                )
            )
        if orm is None:
            raise SearchToolConfigNotFoundError(
                f"Default graph search config missing for workspace '{workspace_id}'."
            )
        return str(orm.id)

    def _upsert_system_config(
        self,
        session,  # noqa: ANN001
        *,
        workspace_id: str,
        tool_type: str,
        system_key: str,
        name: str,
        description: str,
        embedding_provider: str,
        embedding_model: str,
        default_top_k: int,
        created_at: datetime,
        collection_target: str = "workspace",
        bm25_enabled: bool = False,
        fusion_strategy: str = "semantic_only",
        ontology_scope: str = "published",
        graph_search_type: str = "combined",
        reranker: str = "rrf",
    ) -> SearchToolConfigORM:
        existing = session.scalar(
            select(SearchToolConfigORM).where(
                SearchToolConfigORM.workspace_id == workspace_id,
                SearchToolConfigORM.system_key == system_key,
            )
        )
        resolved_version_id = None
        if tool_type == "graph":
            resolved_version_id = self._latest_ontology_version_id(session, workspace_id)
        if existing is None:
            existing = SearchToolConfigORM(
                id=str(uuid4()),
                workspace_id=workspace_id,
                tool_type=tool_type,
                name=name,
                description=description,
                system_key=system_key,
                is_system=True,
                provider=embedding_provider,
                model=embedding_model,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                default_top_k=default_top_k,
                collection_target=collection_target,
                document_ids=[],
                bm25_enabled=bm25_enabled,
                fusion_strategy=fusion_strategy,
                ontology_scope=ontology_scope,
                ontology_version_id=resolved_version_id,
                graph_search_type=graph_search_type,
                reranker=reranker,
                config_metadata={},
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(existing)
        else:
            existing.name = name
            existing.description = description
            existing.is_system = True
            existing.provider = embedding_provider
            existing.model = embedding_model
            existing.embedding_provider = embedding_provider
            existing.embedding_model = embedding_model
            existing.default_top_k = default_top_k
            if tool_type == "docs":
                existing.collection_target = collection_target
                existing.bm25_enabled = bm25_enabled
                existing.fusion_strategy = fusion_strategy
            else:
                existing.ontology_scope = ontology_scope
                existing.ontology_version_id = resolved_version_id
                existing.graph_search_type = graph_search_type
                existing.reranker = reranker
            existing.updated_at = created_at
        session.flush()
        return existing

    def _ensure_ontology_index(
        self,
        *,
        workspace_id: str,
        version_id: str,
        embedding_provider: str,
        embedding_model: str,
    ) -> None:
        with self._database_manager.session() as session:
            existing = session.scalar(
                select(OntologySearchIndexORM).where(
                    OntologySearchIndexORM.workspace_id == workspace_id,
                    OntologySearchIndexORM.version_id == version_id,
                    OntologySearchIndexORM.embedding_provider == embedding_provider,
                    OntologySearchIndexORM.embedding_model == embedding_model,
                )
            )
            if existing is not None:
                return
        self._rebuild_ontology_index(
            workspace_id=workspace_id,
            version_id=version_id,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )

    def _rebuild_ontology_index(
        self,
        *,
        workspace_id: str,
        version_id: str,
        embedding_provider: str,
        embedding_model: str,
    ) -> None:
        now = _utc_now()
        with self._database_manager.session() as session:
            session.execute(
                delete(OntologySearchIndexORM).where(
                    OntologySearchIndexORM.workspace_id == workspace_id,
                    OntologySearchIndexORM.version_id == version_id,
                    OntologySearchIndexORM.embedding_provider == embedding_provider,
                    OntologySearchIndexORM.embedding_model == embedding_model,
                )
            )
            entities = session.scalars(
                select(OntologyEntityORM).where(
                    OntologyEntityORM.workspace_id == workspace_id,
                    OntologyEntityORM.version_id == version_id,
                )
            ).all()
            relations = session.scalars(
                select(OntologyRelationORM).where(
                    OntologyRelationORM.workspace_id == workspace_id,
                    OntologyRelationORM.version_id == version_id,
                )
            ).all()
            entity_facts = session.scalars(
                select(OntologyEntityFactORM).where(
                    OntologyEntityFactORM.workspace_id == workspace_id,
                    OntologyEntityFactORM.version_id == version_id,
                )
            ).all()
            relation_facts = session.scalars(
                select(OntologyRelationFactORM).where(
                    OntologyRelationFactORM.workspace_id == workspace_id,
                    OntologyRelationFactORM.version_id == version_id,
                )
            ).all()
            items: list[tuple[str, str, str, str]] = []
            items.extend(
                (
                    "entity",
                    entity.id,
                    entity.name,
                    " ".join(filter(None, [entity.name, entity.entity_type, *(entity.aliases or [])])),
                )
                for entity in entities
            )
            items.extend(
                (
                    "relation",
                    relation.id,
                    relation.relation_type,
                    " ".join(
                        filter(None, [relation.relation_type, relation.evidence_text])
                    ),
                )
                for relation in relations
            )
            items.extend(
                (
                    "entity_fact",
                    fact.id,
                    f"Fact: {fact.metric_key}",
                    " ".join(
                        filter(
                            None,
                            [
                                fact.metric_key,
                                fact.value_text,
                                str(fact.value_num) if fact.value_num is not None else None,
                                fact.unit,
                            ],
                        )
                    ),
                )
                for fact in entity_facts
            )
            items.extend(
                (
                    "relation_fact",
                    fact.id,
                    f"Fact: {fact.metric_key}",
                    " ".join(
                        filter(
                            None,
                            [
                                fact.metric_key,
                                fact.value_text,
                                str(fact.value_num) if fact.value_num is not None else None,
                                fact.unit,
                            ],
                        )
                    ),
                )
                for fact in relation_facts
            )
            for item_type, item_id, title, content in items:
                embedding = self._retrieval_service.embed_text(
                    content,
                    workspace_id=workspace_id,
                    provider=embedding_provider,
                    model=embedding_model,
                )
                session.add(
                    OntologySearchIndexORM(
                        id=str(uuid4()),
                        workspace_id=workspace_id,
                        version_id=version_id,
                        item_type=item_type,
                        item_id=item_id,
                        title=title,
                        content=content,
                        embedding=embedding,
                        embedding_provider=embedding_provider,
                        embedding_model=embedding_model,
                        created_at=now,
                        updated_at=now,
                    )
                )

    @staticmethod
    def _latest_ontology_version_id(session, workspace_id: str) -> str | None:  # noqa: ANN001
        latest = session.scalar(
            select(OntologyVersionORM)
            .where(OntologyVersionORM.workspace_id == workspace_id)
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
        if not (orm.embedding_provider or "").strip():
            raise SearchToolConfigInvalidError("embedding_provider is required.")
        if not (orm.embedding_model or "").strip():
            raise SearchToolConfigInvalidError("embedding_model is required.")

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

    def _resolve_embedding_fields(
        self,
        workspace_id: str,
        *,
        embedding_provider: str | None,
        embedding_model: str | None,
    ) -> tuple[str, str]:
        resolved_provider = (embedding_provider or FORCED_EMBEDDING_PROVIDER).strip()
        resolved_model = (embedding_model or FORCED_EMBEDDING_MODEL).strip()
        if not resolved_provider or not resolved_model:
            raise SearchToolConfigInvalidError(
                "Search tool configs require embedding_provider and embedding_model."
            )
        return resolved_provider, resolved_model

    @staticmethod
    def _resolve_knowledge_pack_ids(config: SearchToolConfigResponse) -> list[str] | None:
        raw_value = (config.config_metadata or {}).get("knowledge_pack_ids")
        if not isinstance(raw_value, list):
            return None
        values = [str(item).strip() for item in raw_value if str(item).strip()]
        return values or None

    def _graphiti_group_ids_for_config(self, config: SearchToolConfigResponse) -> list[str]:
        """Graphiti ``group_ids``: legacy workspace string, or projections from config metadata."""
        base = [config.workspace_id]
        svc = self._ontology_graph_projection_service
        if svc is None:
            return base
        raw = (config.config_metadata or {}).get("ontology_graph_projection_ids")
        if not isinstance(raw, list):
            return base
        ids = [str(item).strip() for item in raw if str(item).strip()]
        if not ids:
            return base
        try:
            return svc.projection_group_ids_for_search(workspace_id=config.workspace_id, projection_row_ids=ids)
        except OntologyGraphProjectionError as exc:
            raise SearchToolConfigInvalidError(str(exc)) from exc

    @staticmethod
    def _next_duplicate_name(
        session,  # noqa: ANN001
        *,
        workspace_id: str,
        tool_type: str,
        base_name: str,
    ) -> str:
        attempt = f"{base_name} Copy"
        suffix = 2
        while session.scalar(
            select(SearchToolConfigORM).where(
                SearchToolConfigORM.workspace_id == workspace_id,
                SearchToolConfigORM.tool_type == tool_type,
                SearchToolConfigORM.name == attempt,
            )
        ):
            attempt = f"{base_name} Copy {suffix}"
            suffix += 1
        return attempt

    def _to_response(self, orm: SearchToolConfigORM) -> SearchToolConfigResponse:
        ready, reason = self._model_config_service.embedding_backend_status(
            orm.embedding_provider,
            orm.embedding_model,
            orm.workspace_id,
        )
        if not ready:
            reason = f"Embedding backend not ready: {reason}"
        return SearchToolConfigResponse(
            id=orm.id,
            workspace_id=orm.workspace_id,
            tool_type=orm.tool_type,  # type: ignore[arg-type]
            name=orm.name,
            description=orm.description or "",
            provider=orm.provider or orm.embedding_provider,
            model=orm.model or orm.embedding_model,
            tool_name=TOOL_NAME_DOCS if orm.tool_type == "docs" else TOOL_NAME_GRAPH,
            embedding_provider=orm.embedding_provider,
            embedding_model=orm.embedding_model,
            default_top_k=orm.default_top_k,
            system_key=orm.system_key,
            is_system=bool(orm.is_system),
            assignable_slots=["rag"] if orm.tool_type == "docs" else ["ontology_search"],
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


__all__ = [
    "SearchToolConfigService",
    "SearchToolConfigNotFoundError",
    "SearchToolConfigInvalidError",
    "SearchToolSystemManagedError",
    "TOOL_NAME_DOCS",
    "TOOL_NAME_GRAPH",
]
