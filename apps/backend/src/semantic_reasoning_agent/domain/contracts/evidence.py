from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Mapping
from uuid import UUID

EvidenceKind = Literal["extraction", "retrieval", "graph", "web", "user", "artifact"]


@dataclass(frozen=True)
class CitationAnchor:
    document_id: UUID | None
    chunk_id: UUID | None = None
    page: int | None = None
    section: str | None = None
    sheet_name: str | None = None
    row_range: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    label: str | None = None


@dataclass(frozen=True)
class Evidence:
    evidence_id: UUID
    kind: EvidenceKind
    produced_by_tool: str
    workflow_run_id: UUID | None
    anchors: tuple[CitationAnchor, ...]
    payload: Mapping[str, Any]
    created_at: datetime
    confidence: float | None = None
    trust_score: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
