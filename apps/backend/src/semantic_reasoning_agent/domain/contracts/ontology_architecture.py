from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class OntologyArchitectureType:
    name: str
    description: str
    attributes: tuple[dict[str, Any], ...] = ()
    source_targets: tuple[dict[str, str], ...] = ()
    normalization_hints: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OntologyArchitectureEvidenceLink:
    link_kind: str
    target_name: str
    source_chunk_id: str | None
    source_document_id: str | None
    evidence_text: str
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OntologyArchitectureReview:
    summary: str
    findings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "findings": list(self.findings),
        }


@dataclass(frozen=True, slots=True)
class OntologyArchitectureDraft:
    draft_id: str
    workspace_id: str
    source_document_ids: tuple[str, ...]
    domain: str
    status: str
    entity_types: tuple[OntologyArchitectureType, ...] = ()
    relation_types: tuple[OntologyArchitectureType, ...] = ()
    normalization_hints: tuple[dict[str, Any], ...] = ()
    workflow_hints: tuple[str, ...] = ()
    tool_affinity_hints: tuple[str, ...] = ()
    review: OntologyArchitectureReview | None = None
    evidence_links: tuple[OntologyArchitectureEvidenceLink, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "workspace_id": self.workspace_id,
            "source_document_ids": list(self.source_document_ids),
            "domain": self.domain,
            "status": self.status,
            "entity_types": [item.to_dict() for item in self.entity_types],
            "relation_types": [item.to_dict() for item in self.relation_types],
            "normalization_hints": list(self.normalization_hints),
            "workflow_hints": list(self.workflow_hints),
            "tool_affinity_hints": list(self.tool_affinity_hints),
            "review": None if self.review is None else self.review.to_dict(),
            "evidence_links": [item.to_dict() for item in self.evidence_links],
            "provenance": dict(self.provenance),
            "created_at": None if self.created_at is None else self.created_at.isoformat(),
            "updated_at": None if self.updated_at is None else self.updated_at.isoformat(),
        }
