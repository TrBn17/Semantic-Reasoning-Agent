from __future__ import annotations

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.infrastructure.graph.neo4j_graph_store import Neo4jGraphStore
from semantic_reasoning_agent.infrastructure.graph.null_graph_store import NullGraphStore
from semantic_reasoning_agent.ports.graph_store import GraphStore


def build_graph_store(settings: Settings) -> GraphStore:
    if not settings.neo4j_enabled:
        return NullGraphStore()
    return Neo4jGraphStore(settings)


__all__ = ["NullGraphStore", "Neo4jGraphStore", "build_graph_store"]
