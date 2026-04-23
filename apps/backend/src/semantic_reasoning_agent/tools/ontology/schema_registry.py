from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.persistence.repositories.ontology_repo import OntologyRepository


@dataclass(frozen=True)
class EmergentSchema:
    """The descriptive set of types observed across past builds for a workspace.

    Fed to the LLM extractor as a *prior* — types the model is encouraged to
    reuse when they fit. Never a constraint: the LLM may propose new types
    on every call. The registry never rejects novel types.
    """

    workspace_id: str
    entity_types: tuple[str, ...]
    relation_types: tuple[str, ...]


class OntologySchemaRegistry:
    """Reads emergent entity/relation types from published ontology state.

    No hardcoded vocabulary. The schema for each workspace is the union of
    entity/relation type names already published for that workspace.
    """

    def __init__(self, ontology_repo: OntologyRepository) -> None:
        self._repo = ontology_repo

    def for_workspace(self, workspace_id: str) -> EmergentSchema:
        return EmergentSchema(
            workspace_id=workspace_id,
            entity_types=tuple(self._repo.list_used_entity_types(workspace_id)),
            relation_types=tuple(self._repo.list_used_relation_types(workspace_id)),
        )
