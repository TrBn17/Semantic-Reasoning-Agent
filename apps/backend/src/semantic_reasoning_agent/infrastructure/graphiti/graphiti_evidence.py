"""Map Graphiti search matches to domain Evidence (single place for graphiti.search consumers)."""

from __future__ import annotations

from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiSearchMatch



def graphiti_matches_to_evidence(
    matches: list[GraphitiSearchMatch],
    *,
    workspace_id: str,
    tool_call_id: UUID,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    for match in matches:
        if match.kind == "edge":
            evidence.append(
                map_edge_to_evidence(
                    match.item,
                    workspace_id=workspace_id,
                    tool_call_id=tool_call_id,
                    score=match.score,
                )
            )
        else:
            evidence.append(
                map_node_to_evidence(
                    match.item,
                    workspace_id=workspace_id,
                    tool_call_id=tool_call_id,
                    score=match.score,
                )
            )
    return evidence
