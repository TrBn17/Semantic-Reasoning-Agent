"""Stable Graphiti `group_id` strings: one ontology graph projection ⇒ one partitioned graph (like a RAG collection)."""

from __future__ import annotations


def legacy_workspace_graphiti_group(workspace_id: str) -> str:
    """Historical behavior: the whole Neo4j partition keyed by workspace id."""
    return workspace_id


def graphiti_group_id_for_projection(workspace_id: str, projection_id: str) -> str:
    """Neo4j/Graphiti `group_id` for a scoped ontology graph under one knowledge pack."""
    ws = workspace_id.strip()
    pid = projection_id.strip()
    return f"w:{ws}:og:{pid}"
