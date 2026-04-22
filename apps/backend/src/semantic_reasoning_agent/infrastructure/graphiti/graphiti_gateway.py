from __future__ import annotations

import asyncio
import inspect
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from semantic_reasoning_agent.core.config import Settings


@dataclass(frozen=True)
class GraphitiSearchMatch:
    kind: str
    item: Any
    score: float


SearchType = Literal["nodes", "edges", "combined"]
RerankerMode = Literal["cross_encoder", "rrf", "none"]


class GraphitiGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._graphiti = None
        self._load_error: str | None = None

    def is_enabled(self) -> bool:
        return bool(self._settings.graphiti_enabled and self._settings.neo4j_enabled)

    def ensure_indices(self) -> None:
        graphiti = self._require_graphiti()
        self._run_async(graphiti.build_indices_and_constraints())

    def search(
        self,
        *,
        query: str,
        workspace_id: str,
        limit: int = 5,
        search_type: SearchType = "combined",
        center_node_uuid: str | None = None,
        valid_at: datetime | None = None,
        reranker: RerankerMode = "cross_encoder",
    ) -> list[GraphitiSearchMatch]:
        if not self.is_enabled():
            return []
        graphiti = self._require_graphiti()
        results = self._execute_search(
            graphiti,
            query=query,
            workspace_id=workspace_id,
            limit=limit,
            search_type=search_type,
            center_node_uuid=center_node_uuid,
            valid_at=valid_at,
            reranker=reranker,
        )

        matches: list[GraphitiSearchMatch] = []
        for index, edge in enumerate(getattr(results, "edges", ()) or ()):
            score = 0.0
            edge_scores = getattr(results, "edge_reranker_scores", ()) or ()
            if index < len(edge_scores):
                score = float(edge_scores[index])
            matches.append(GraphitiSearchMatch(kind="edge", item=edge, score=score))
        for index, node in enumerate(getattr(results, "nodes", ()) or ()):
            score = 0.0
            node_scores = getattr(results, "node_reranker_scores", ()) or ()
            if index < len(node_scores):
                score = float(node_scores[index])
            matches.append(GraphitiSearchMatch(kind="node", item=node, score=score))
        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:limit]

    def _execute_search(
        self,
        graphiti: Any,
        *,
        query: str,
        workspace_id: str,
        limit: int,
        search_type: SearchType,
        center_node_uuid: str | None,
        valid_at: datetime | None,
        reranker: RerankerMode,
    ) -> Any:
        sig = inspect.signature(graphiti.search_)
        if "config" not in sig.parameters:
            return self._run_async(graphiti.search_(query=query, group_ids=[workspace_id]))

        try:
            from graphiti_core.search.search_config_recipes import (  # type: ignore
                COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
                COMBINED_HYBRID_SEARCH_RRF,
                EDGE_HYBRID_SEARCH_CROSS_ENCODER,
                EDGE_HYBRID_SEARCH_RRF,
                NODE_HYBRID_SEARCH_CROSS_ENCODER,
                NODE_HYBRID_SEARCH_RRF,
            )
            from graphiti_core.search.search_filters import (  # type: ignore
                ComparisonOperator,
                DateFilter,
                SearchFilters,
            )
        except Exception:  # noqa: BLE001
            return self._run_async(graphiti.search_(query=query, group_ids=[workspace_id]))

        use_rrf = reranker in ("rrf", "none")
        use_cross = reranker == "cross_encoder"

        if search_type == "nodes":
            base = (
                NODE_HYBRID_SEARCH_RRF
                if use_rrf
                else NODE_HYBRID_SEARCH_CROSS_ENCODER
                if use_cross
                else NODE_HYBRID_SEARCH_RRF
            )
        elif search_type == "edges":
            base = (
                EDGE_HYBRID_SEARCH_RRF
                if use_rrf
                else EDGE_HYBRID_SEARCH_CROSS_ENCODER
                if use_cross
                else EDGE_HYBRID_SEARCH_RRF
            )
        else:
            base = (
                COMBINED_HYBRID_SEARCH_RRF
                if use_rrf
                else COMBINED_HYBRID_SEARCH_CROSS_ENCODER
                if use_cross
                else COMBINED_HYBRID_SEARCH_RRF
            )

        config = base.model_copy(update={"limit": max(1, int(limit))})

        search_filter: Any
        if valid_at is not None:
            search_filter = SearchFilters(
                valid_at=[
                    [
                        DateFilter(
                            date=valid_at,
                            comparison_operator=ComparisonOperator.less_than_equal,
                        )
                    ]
                ]
            )
        else:
            search_filter = SearchFilters()

        return self._run_async(
            graphiti.search_(
                query,
                config,
                [workspace_id],
                center_node_uuid,
                None,
                search_filter,
            )
        )

    def ingest_episode(
        self,
        *,
        name: str,
        episode_body: str,
        source_description: str,
        workspace_id: str,
        reference_time: datetime | None = None,
    ) -> dict[str, str]:
        if not self.is_enabled():
            return {}
        graphiti = self._require_graphiti()
        result = self._run_async(
            graphiti.add_episode(
                name=name,
                episode_body=episode_body,
                source_description=source_description,
                reference_time=reference_time or datetime.now(timezone.utc),
                group_id=workspace_id,
            )
        )
        episode = getattr(result, "episode", None)
        return {"episode_uuid": getattr(episode, "uuid", "")} if episode is not None else {}

    def upsert_node(
        self,
        *,
        uuid: str,
        name: str,
        entity_type: str,
        aliases: list[str],
        workspace_id: str,
        source_document_id: str | None = None,
    ) -> None:
        """Materialize a standalone ontology entity in Graphiti via an episodic ingest."""
        if not self.is_enabled():
            return
        payload = {
            "kind": "ontology_entity",
            "id": uuid,
            "name": name,
            "entity_type": entity_type,
            "aliases": aliases,
            "source_document_id": source_document_id,
        }
        body = json.dumps(payload, ensure_ascii=False)[:120_000]
        self.ingest_episode(
            name=f"ontology-entity-{uuid}",
            episode_body=body,
            source_description="ontology_publish_entity",
            workspace_id=workspace_id,
            reference_time=datetime.now(timezone.utc),
        )

    def upsert_edge(
        self,
        *,
        uuid: str,
        source_uuid: str,
        target_uuid: str,
        source_name: str,
        target_name: str,
        relation_type: str,
        fact: str,
        valid_at: datetime | None,
        workspace_id: str,
        source_entity_type: str = "Entity",
        target_entity_type: str = "Entity",
    ) -> None:
        """Upsert a typed relation between two ontology entities using Graphiti ``add_triplet``."""
        if not self.is_enabled():
            return
        graphiti = self._require_graphiti()
        try:
            from graphiti_core.edges import EntityEdge  # type: ignore
            from graphiti_core.nodes import EntityNode  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Graphiti SDK missing node/edge models: {exc}") from exc

        now = datetime.now(timezone.utc)
        src = EntityNode(
            uuid=source_uuid,
            name=source_name or source_uuid,
            group_id=workspace_id,
            labels=[],
            attributes={"ontology_entity_type": source_entity_type},
        )
        tgt = EntityNode(
            uuid=target_uuid,
            name=target_name or target_uuid,
            group_id=workspace_id,
            labels=[],
            attributes={"ontology_entity_type": target_entity_type},
        )
        edge = EntityEdge(
            uuid=uuid,
            group_id=workspace_id,
            source_node_uuid=source_uuid,
            target_node_uuid=target_uuid,
            created_at=now,
            name=relation_type,
            fact=fact or f"{source_name} {relation_type} {target_name}",
            valid_at=valid_at,
        )
        self._run_async(graphiti.add_triplet(src, edge, tgt))

    def status_detail(self) -> str | None:
        return self._load_error

    def _require_graphiti(self):
        if self._graphiti is not None:
            return self._graphiti
        if not self.is_enabled():
            raise RuntimeError("Graphiti is disabled.")

        graphiti_root = _discover_graphiti_root()
        if graphiti_root is not None and str(graphiti_root) not in sys.path:
            sys.path.insert(0, str(graphiti_root))

        try:
            from graphiti_core import Graphiti  # type: ignore
            from graphiti_core.driver.neo4j_driver import Neo4jDriver  # type: ignore
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc) or exc.__class__.__name__
            raise RuntimeError(f"Failed to import Graphiti SDK: {self._load_error}") from exc

        try:
            driver = Neo4jDriver(
                uri=self._settings.neo4j_uri,
                user=self._settings.neo4j_user,
                password=self._settings.neo4j_password,
                database=self._settings.graphiti_database or self._settings.neo4j_database,
            )
            self._graphiti = Graphiti(graph_driver=driver)
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc) or exc.__class__.__name__
            raise RuntimeError(f"Failed to initialize Graphiti: {self._load_error}") from exc
        return self._graphiti

    @staticmethod
    def _run_async(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="graphiti-async-bridge") as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()


def _discover_graphiti_root() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "graphiti"
        if candidate.exists() and (candidate / "graphiti_core").exists():
            return candidate
    return None
