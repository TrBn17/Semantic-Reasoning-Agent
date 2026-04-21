from __future__ import annotations

from semantic_reasoning_agent.domain.contracts.published_ontology_snapshot import PublishedOntologySnapshot
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway


class OntologyGraphPublisherError(RuntimeError):
    """Raised when the runtime graph cannot be prepared during publish."""


class OntologyGraphPublisher:
    def __init__(self, graphiti_gateway: GraphitiGateway) -> None:
        self._graphiti_gateway = graphiti_gateway
        self.last_published_snapshot: PublishedOntologySnapshot | None = None

    def is_enabled(self) -> bool:
        return self._graphiti_gateway.is_enabled()

    def publish(self, snapshot: PublishedOntologySnapshot | None = None) -> None:
        self.last_published_snapshot = snapshot
        if not self._graphiti_gateway.is_enabled():
            return
        try:
            self._graphiti_gateway.ensure_indices()
        except Exception as exc:  # noqa: BLE001
            raise OntologyGraphPublisherError(str(exc) or exc.__class__.__name__) from exc
