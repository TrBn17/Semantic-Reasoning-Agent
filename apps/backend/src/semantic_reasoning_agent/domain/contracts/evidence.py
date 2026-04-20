from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

SourceType = Literal[
    "internal_chunk",
    "web_page",
    "graph_node",
    "graph_edge",
    "mcp_result",
    "generated_artifact",
]

AnchorType = Literal[
    "page",
    "section",
    "sheet_row",
    "url_fragment",
    "graph_ref",
    "artifact_ref",
]


@dataclass(frozen=True)
class CitationAnchor:
    """Structured pointer inside a source — AGENTS.md §9 Citation Anchor Model.

    One anchor per Evidence. Anchor type chooses the interpretation of ``locator``
    (e.g. a page number, a heading path, a sheet row range, a URL fragment, or
    a graph node/edge id). ``label`` is the human-readable rendering.
    """

    anchor_type: AnchorType
    label: str
    locator: str


@dataclass(frozen=True)
class Provenance:
    """Provenance metadata attached to every piece of evidence — §9."""

    workspace_id: str
    captured_at: datetime
    source_id: str | None = None
    tool_call_id: UUID | None = None
    parser_version: str | None = None
    extractor_version: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class Evidence:
    """Unified Evidence Contract — AGENTS.md §9.

    Every extracted, retrieved, or generated unit surfaced back to the runtime
    MUST conform to this shape regardless of which tool produced it.
    """

    evidence_id: UUID
    source_type: SourceType
    title: str
    content: str
    citation_anchor: CitationAnchor
    provenance: Provenance
    summary: str | None = None
    uri: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    page: int | None = None
    section: str | None = None
    sheet_name: str | None = None
    row_range: str | None = None
    entity_ids: tuple[str, ...] = ()
    relation_ids: tuple[str, ...] = ()
    score: float = 0.0
    trust_score: float = 0.0
    freshness_ts: datetime | None = None
