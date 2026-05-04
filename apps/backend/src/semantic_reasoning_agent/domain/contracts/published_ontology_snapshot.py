from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.schemas.ontology import (
    OntologyEntityResponse,
    OntologyEntityTypeDefinitionResponse,
    OntologyRelationResponse,
    OntologyRelationTypeDefinitionResponse,
    OntologyVersionResponse,
)


@dataclass(slots=True)
class PublishedOntologySnapshot:
    workspace_id: str
    version: OntologyVersionResponse | None
    entity_type_definitions: list[OntologyEntityTypeDefinitionResponse]
    relation_type_definitions: list[OntologyRelationTypeDefinitionResponse]
    entities: list[OntologyEntityResponse]
    relations: list[OntologyRelationResponse]
    #: When set, Graphiti ``group_id`` (partition) for this publish; otherwise legacy ``workspace_id``.
    graphiti_group_id: str | None = None
