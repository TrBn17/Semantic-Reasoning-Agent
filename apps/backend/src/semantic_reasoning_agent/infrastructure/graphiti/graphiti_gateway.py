from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from semantic_reasoning_agent.core.config import Settings


@dataclass(frozen=True)
class GraphitiSearchMatch:
    kind: str
    item: Any
    score: float


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
    ) -> list[GraphitiSearchMatch]:
        if not self.is_enabled():
            return []
        graphiti = self._require_graphiti()
        results = self._run_async(graphiti.search_(query=query, group_ids=[workspace_id]))

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
                database=self._settings.graphiti_database,
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
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def _discover_graphiti_root() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "graphiti"
        if candidate.exists() and (candidate / "graphiti_core").exists():
            return candidate
    return None
