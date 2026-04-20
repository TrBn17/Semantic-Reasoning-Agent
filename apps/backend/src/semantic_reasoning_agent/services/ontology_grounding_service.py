from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.domain.contracts.tool_envelope import OntologyContextRef
from semantic_reasoning_agent.services.ontology_architecture_service import (
    ArchitectureGrounding,
    OntologyArchitectureService,
)
from semantic_reasoning_agent.services.ontology_errors import OntologyGraphError
from semantic_reasoning_agent.services.ontology_service import OntologyService


@dataclass(frozen=True, slots=True)
class TaskOntologyGrounding:
    architecture: ArchitectureGrounding
    published_domain: str | None
    published_entity_hints: tuple[str, ...]
    published_relation_hints: tuple[str, ...]

    def as_context_ref(self) -> OntologyContextRef:
        entity_hints = tuple(
            dict.fromkeys(self.architecture.entity_hints + self.published_entity_hints)
        )[:20]
        relation_hints = tuple(
            dict.fromkeys(self.architecture.relation_hints + self.published_relation_hints)
        )[:20]
        domain = self.architecture.domain or self.published_domain
        return OntologyContextRef(
            domain=domain,
            entity_hints=entity_hints,
            relation_hints=relation_hints,
            normalization_rules=self.architecture.normalization_rules,
        )


class OntologyGroundingService:
    def __init__(
        self,
        *,
        ontology_service: OntologyService,
        ontology_architecture_service: OntologyArchitectureService,
    ) -> None:
        self._ontology_service = ontology_service
        self._ontology_architecture_service = ontology_architecture_service

    def ground_workspace(self, workspace_id: str) -> TaskOntologyGrounding:
        architecture = self._ontology_architecture_service.build_grounding(workspace_id)
        published_domain = None
        entity_hints: tuple[str, ...] = ()
        relation_hints: tuple[str, ...] = ()
        try:
            graph = self._ontology_service.get_graph(workspace_id=workspace_id)
        except OntologyGraphError:
            graph = None
        if graph is not None:
            if graph.version is not None:
                published_domain = f"published_v{graph.version.version_number}"
            entity_hints = tuple(
                sorted({entity.entity_type for entity in graph.entities if entity.entity_type})
            )
            relation_hints = tuple(
                sorted({relation.relation_type for relation in graph.relations if relation.relation_type})
            )
        return TaskOntologyGrounding(
            architecture=architecture,
            published_domain=published_domain,
            published_entity_hints=entity_hints,
            published_relation_hints=relation_hints,
        )
