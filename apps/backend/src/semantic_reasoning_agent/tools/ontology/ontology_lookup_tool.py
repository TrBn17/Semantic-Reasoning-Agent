from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.schemas.ontology import (
    OntologyEntityResponse,
    OntologyGraphResponse,
    OntologyRelationResponse,
)
from semantic_reasoning_agent.services.ontology_service import (
    OntologyGraphError,
    OntologyService,
)
from semantic_reasoning_agent.tools.base import Tool


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "mode": {
            "type": "string",
            "enum": ["published_graph", "current_version", "entity_lookup"],
            "default": "published_graph",
            "description": (
                "published_graph: all entities + relations of the latest published version. "
                "current_version: metadata only. entity_lookup: filter by substring in 'query'."
            ),
        },
        "query": {
            "type": "string",
            "description": "Case-insensitive substring used when mode='entity_lookup'.",
        },
    },
    "required": [],
    "additionalProperties": False,
}


class OntologyLookupTool(Tool):
    """Read the current published ontology version — AGENTS.md §9 / §14.

    Entities become ``graph_node`` Evidence, relations become ``graph_edge``
    Evidence. Types are surfaced directly from the published rows (never
    hardcoded), preserving the LLM-first ontology rule.
    """

    tool_name = "ontology.lookup"

    SPEC = ToolSpec(
        tool_name="ontology.lookup",
        tool_family="ontology",
        tool_type="internal_service",
        version="1.0.0",
        description=(
            "Reads the workspace's current published ontology: entities, "
            "relations, and version metadata. Returns graph nodes and edges "
            "as Evidence."
        ),
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:ontology.lookup.in.v1",
        capabilities=("schema_lookup", "graph_read"),
        risk_level="low",
        side_effect_level="read_only",
        supports_parallel=True,
        timeout_ms=10000,
    )

    def __init__(self, ontology_service: OntologyService) -> None:
        self._ontology_service = ontology_service

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments if isinstance(envelope.arguments, dict) else {}
        mode = arguments.get("mode", "published_graph")
        query = arguments.get("query", "")
        if not isinstance(query, str):
            query = ""

        try:
            graph = self._ontology_service.get_graph(workspace_id=envelope.workspace_id)
        except OntologyGraphError as exc:
            raise RuntimeError(f"ontology.lookup graph read failed: {exc}") from exc

        now = datetime.now(timezone.utc)

        if mode == "current_version":
            return _current_version_result(envelope, graph, now)

        entities = graph.entities
        relations = graph.relations
        if mode == "entity_lookup" and query.strip():
            needle = query.strip().lower()
            entities = [e for e in entities if needle in e.name.lower() or needle in e.entity_type.lower()]
            entity_ids = {e.id for e in entities}
            relations = [
                r for r in relations
                if r.source_entity_id in entity_ids or r.target_entity_id in entity_ids
            ]

        evidence: list[Evidence] = []
        for entity in entities:
            evidence.append(_entity_to_evidence(entity, envelope=envelope, captured_at=now))
        for relation in relations:
            evidence.append(_relation_to_evidence(relation, envelope=envelope, captured_at=now))

        status = "success" if evidence else "partial"
        hints: tuple[str, ...] = () if evidence else ("no_published_ontology",)

        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status=status,
            started_at=now,
            finished_at=now,
            latency_ms=0,
            evidence=tuple(evidence),
            next_action_hints=hints,
            meta=ToolMeta(),
        )


def _current_version_result(
    envelope: ToolEnvelope,
    graph: OntologyGraphResponse,
    now: datetime,
) -> ToolResult:
    version = graph.version
    if version is None:
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=OntologyLookupTool.tool_name,
            status="partial",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            next_action_hints=("no_published_ontology",),
            meta=ToolMeta(),
        )
    summary_payload = {
        "version_id": version.id,
        "version_number": version.version_number,
        "workspace_id": version.workspace_id,
        "entity_count": version.entity_count,
        "relation_count": version.relation_count,
        "created_at": version.created_at.isoformat(),
    }
    return ToolResult(
        call_id=envelope.call_id,
        tool_name=OntologyLookupTool.tool_name,
        status="success",
        started_at=now,
        finished_at=now,
        latency_ms=0,
        artifacts=(summary_payload,),
        meta=ToolMeta(),
    )


def _entity_to_evidence(
    entity: OntologyEntityResponse,
    *,
    envelope: ToolEnvelope,
    captured_at: datetime,
) -> Evidence:
    aliases = ", ".join(entity.aliases) if entity.aliases else ""
    content = f"{entity.name} (type: {entity.entity_type})"
    if aliases:
        content = f"{content} — aliases: {aliases}"
    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_node",
        title=entity.name,
        content=content,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=entity.entity_type,
            locator=f"entity:{entity.id}",
        ),
        provenance=Provenance(
            workspace_id=envelope.workspace_id,
            source_id=entity.source_document_id,
            tool_call_id=envelope.call_id,
            captured_at=captured_at,
        ),
        entity_ids=(entity.id,),
    )


def _relation_to_evidence(
    relation: OntologyRelationResponse,
    *,
    envelope: ToolEnvelope,
    captured_at: datetime,
) -> Evidence:
    content = (
        f"{relation.source_entity_id} --[{relation.relation_type}]-> "
        f"{relation.target_entity_id}"
    )
    if relation.evidence_text:
        content = f"{content} :: {relation.evidence_text}"

    entity_ids_raw: list[str] = []
    for candidate in (relation.source_entity_id, relation.target_entity_id):
        if candidate:
            entity_ids_raw.append(candidate)
    relation_ids_raw = (relation.id,) if relation.id else ()

    return Evidence(
        evidence_id=uuid4(),
        source_type="graph_edge",
        title=relation.relation_type,
        content=content,
        citation_anchor=CitationAnchor(
            anchor_type="graph_ref",
            label=relation.relation_type,
            locator=f"relation:{relation.id}",
        ),
        provenance=Provenance(
            workspace_id=envelope.workspace_id,
            source_id=relation.source_document_id,
            tool_call_id=envelope.call_id,
            captured_at=captured_at,
        ),
        score=relation.confidence,
        entity_ids=tuple(entity_ids_raw),
        relation_ids=relation_ids_raw,
    )
