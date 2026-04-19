from __future__ import annotations

from semantic_reasoning_agent.ports.graph_store import GraphStore, PublishedOntologySnapshot
from semantic_reasoning_agent.schemas.ontology import OntologyGraphResponse


class NullGraphStore(GraphStore):
    def is_enabled(self) -> bool:
        return False

    def verify_connection(self) -> None:
        return None

    def sync_published_graph(self, snapshot: PublishedOntologySnapshot) -> None:
        return None

    def get_graph(self, workspace_id: str) -> OntologyGraphResponse:
        return OntologyGraphResponse(workspace_id=workspace_id)
