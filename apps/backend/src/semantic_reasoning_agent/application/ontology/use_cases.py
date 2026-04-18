from __future__ import annotations

from semantic_reasoning_agent.schemas.ontology import OntologyBuildCreateRequest, OntologyPublishResponse
from semantic_reasoning_agent.services.ontology_service import OntologyService


class OntologyUseCases:
    def __init__(self, service: OntologyService) -> None:
        self._service = service

    def create_build(self, request: OntologyBuildCreateRequest):
        return self._service.create_build(request)

    def process_build(self, build_id: str) -> None:
        self._service.process_build(build_id)

    def publish_build(self, build_id: str) -> OntologyPublishResponse:
        return self._service.publish_build(build_id)
