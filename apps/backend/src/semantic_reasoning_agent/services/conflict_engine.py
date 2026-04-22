from __future__ import annotations

from dataclasses import dataclass, field

from semantic_reasoning_agent.services.context_assembler_service import ContextBundle


@dataclass(frozen=True)
class ConflictItem:
    conflict_type: str
    severity: str
    detail: str


@dataclass(frozen=True)
class ConflictReport:
    conflicts: tuple[ConflictItem, ...] = field(default_factory=tuple)

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicts)


class ConflictEngine:
    def analyze(self, bundle: ContextBundle) -> ConflictReport:
        by_anchor: dict[str, set[str]] = {}
        for citation in bundle.citations:
            key = f"{citation.document_id}:{citation.location_label}"
            by_anchor.setdefault(key, set()).add(citation.excerpt.strip())
        conflicts: list[ConflictItem] = []
        for anchor, excerpts in by_anchor.items():
            if len(excerpts) > 1:
                conflicts.append(
                    ConflictItem(
                        conflict_type="source_disagreement",
                        severity="medium",
                        detail=f"Multiple excerpts differ for {anchor}",
                    )
                )
        return ConflictReport(conflicts=tuple(conflicts))
