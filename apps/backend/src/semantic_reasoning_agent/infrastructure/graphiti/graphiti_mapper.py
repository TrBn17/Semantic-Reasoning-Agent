from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import CitationAnchor, Evidence, Provenance


def map_node_to_evidence(
    node: Any,
    *,
    workspace_id: str,
    tool_call_id,
    score: float = 0.0,
) -> Evidence:
    captured_at = datetime.now(timezone.utc)
    labels = tuple(getattr(node, "labels", ()) or ())
    label = labels[0] if labels else "Entity"
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_node",
        title=getattr(node, "name", "graph-node"),
        content=_node_content(node),
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=label,
            locator=f"graphiti-node:{getattr(node, 'uuid', 'unknown')}",
        ),
        provenance=Provenance(
            workspace_id=workspace_id,
            source_id=getattr(node, "uuid", None),
            tool_call_id=tool_call_id,
            captured_at=captured_at,
        ),
        summary=getattr(node, "summary", None) or None,
        entity_ids=(getattr(node, "uuid", ""),) if getattr(node, "uuid", None) else (),
        score=score,
    )


def map_edge_to_evidence(
    edge: Any,
    *,
    workspace_id: str,
    tool_call_id,
    score: float = 0.0,
) -> Evidence:
    captured_at = datetime.now(timezone.utc)
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_edge",
        title=getattr(edge, "name", "graph-edge"),
        content=_edge_content(edge),
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=getattr(edge, "name", "RELATES_TO"),
            locator=f"graphiti-edge:{getattr(edge, 'uuid', 'unknown')}",
        ),
        provenance=Provenance(
            workspace_id=workspace_id,
            source_id=getattr(edge, "uuid", None),
            tool_call_id=tool_call_id,
            captured_at=captured_at,
        ),
        relation_ids=(getattr(edge, "uuid", ""),) if getattr(edge, "uuid", None) else (),
        entity_ids=tuple(
            value
            for value in (
                getattr(edge, "source_node_uuid", None),
                getattr(edge, "target_node_uuid", None),
            )
            if value
        ),
        freshness_ts=getattr(edge, "reference_time", None),
        score=score,
    )


def _node_content(node: Any) -> str:
    summary = getattr(node, "summary", "") or ""
    if summary:
        return summary
    labels = ", ".join(getattr(node, "labels", ()) or ())
    if labels:
        return f"{getattr(node, 'name', 'graph-node')} [{labels}]"
    return getattr(node, "name", "graph-node")


def _edge_content(edge: Any) -> str:
    fact = getattr(edge, "fact", "") or ""
    if fact:
        return fact
    return (
        f"{getattr(edge, 'source_node_uuid', 'unknown')} --[{getattr(edge, 'name', 'RELATES_TO')}]-> "
        f"{getattr(edge, 'target_node_uuid', 'unknown')}"
    )
