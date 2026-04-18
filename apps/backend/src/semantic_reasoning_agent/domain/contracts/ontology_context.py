from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class OntologyContext:
    """Emergent ontology snapshot passed to extraction tools as a prior.

    Types are descriptive (observed in past builds for the workspace), never
    prescriptive — the extractor may propose new types not in these tuples.
    """

    workspace_id: UUID | None
    ontology_version_id: UUID | None
    version_label: str | None
    entity_types: tuple[str, ...] = ()
    relation_types: tuple[str, ...] = ()
    aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    is_frozen: bool = False
