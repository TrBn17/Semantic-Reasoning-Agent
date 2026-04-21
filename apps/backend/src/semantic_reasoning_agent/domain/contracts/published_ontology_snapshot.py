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
    version: OntologyVersionResponse
    entity_type_definitions: list[OntologyEntityTypeDefinitionResponse]
    relation_type_definitions: list[OntologyRelationTypeDefinitionResponse]
    entities: list[OntologyEntityResponse]
    relations: list[OntologyRelationResponse]
