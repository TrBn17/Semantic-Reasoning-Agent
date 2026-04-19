from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.schemas.ontology import (
    OntologyEntityResponse,
    OntologyGraphResponse,
    OntologyRelationResponse,
    OntologyVersionResponse,
)


@dataclass(slots=True)
class PublishedOntologySnapshot:
    workspace_id: str
    version: OntologyVersionResponse
    entities: list[OntologyEntityResponse]
    relations: list[OntologyRelationResponse]


class GraphStoreError(RuntimeError):
    """Raised when the graph store cannot be reached or updated."""


class GraphStore:
    def is_enabled(self) -> bool:
        raise NotImplementedError

    def verify_connection(self) -> None:
        raise NotImplementedError

    def sync_published_graph(self, snapshot: PublishedOntologySnapshot) -> None:
        raise NotImplementedError

    def get_graph(self, workspace_id: str) -> OntologyGraphResponse:
        raise NotImplementedError
