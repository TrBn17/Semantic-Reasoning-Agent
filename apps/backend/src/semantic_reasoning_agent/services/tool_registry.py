from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from semantic_reasoning_agent.domain.contracts.tool_spec import (
    RiskLevel,
    ToolFamily,
    ToolSpec,
    risk_at_most,
)
from semantic_reasoning_agent.tools.base import Tool

if TYPE_CHECKING:
    from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
    from semantic_reasoning_agent.services.ontology_service import OntologyService
    from semantic_reasoning_agent.services.retrieval_service import RetrievalService


class UnknownToolError(LookupError):
    """Raised when a tool name is not registered."""


class DuplicateToolError(ValueError):
    """Raised when a tool is registered twice under the same name."""


@dataclass
class _Entry:
    spec: ToolSpec
    factory: Callable[[], Tool]


class ToolRegistry:
    """In-memory registry of Tool specs + lazy factories — AGENTS.md §9.

    A factory is called once on first ``get()`` and the instance is cached.
    Specs are retrievable without instantiating the tool, so the registry is
    safe to query from API handlers that only need metadata.
    """

    def __init__(self) -> None:
        self._entries: dict[str, _Entry] = {}
        self._instances: dict[str, Tool] = {}

    def register(self, spec: ToolSpec, factory: Callable[[], Tool]) -> None:
        if spec.tool_name in self._entries:
            raise DuplicateToolError(
                f"Tool '{spec.tool_name}' is already registered."
            )
        self._entries[spec.tool_name] = _Entry(spec=spec, factory=factory)

    def spec(self, name: str) -> ToolSpec | None:
        entry = self._entries.get(name)
        return entry.spec if entry else None

    def get(self, name: str) -> Tool | None:
        entry = self._entries.get(name)
        if entry is None:
            return None
        instance = self._instances.get(name)
        if instance is None:
            instance = entry.factory()
            self._instances[name] = instance
        return instance

    def require(self, name: str) -> Tool:
        tool = self.get(name)
        if tool is None:
            raise UnknownToolError(f"Tool '{name}' is not registered.")
        return tool

    def list(
        self,
        *,
        family: ToolFamily | None = None,
        max_risk: RiskLevel | None = None,
    ) -> list[ToolSpec]:
        specs = [entry.spec for entry in self._entries.values()]
        if family is not None:
            specs = [s for s in specs if s.tool_family == family]
        if max_risk is not None:
            specs = [s for s in specs if risk_at_most(s.risk_level, max_risk)]
        specs.sort(key=lambda s: s.tool_name)
        return specs


def build_tool_registry(
    *,
    retrieval_service: "RetrievalService | None" = None,
    ontology_service: "OntologyService | None" = None,
    graphiti_gateway: "GraphitiGateway | None" = None,
) -> ToolRegistry:
    """Construct a ``ToolRegistry`` and register the Phase-3 tools.

    Services are optional so tests that don't need a wired registry can call
    ``build_tool_registry()`` without arguments and get an empty registry.
    The container always passes both services.
    """
    registry = ToolRegistry()
    if retrieval_service is not None:
        from semantic_reasoning_agent.tools.retrieval.internal_retrieval_tool import (
            InternalRetrievalTool,
        )

        registry.register(
            InternalRetrievalTool.SPEC,
            lambda svc=retrieval_service: InternalRetrievalTool(svc),
        )
    if ontology_service is not None:
        from semantic_reasoning_agent.tools.ontology.ontology_lookup_tool import (
            OntologyLookupTool,
        )

        registry.register(
            OntologyLookupTool.SPEC,
            lambda svc=ontology_service: OntologyLookupTool(svc),
        )
    if graphiti_gateway is not None:
        from semantic_reasoning_agent.tools.graph.graphiti_ingest_tool import GraphitiIngestTool
        from semantic_reasoning_agent.tools.graph.graphiti_search_tool import GraphitiSearchTool

        registry.register(
            GraphitiSearchTool.SPEC,
            lambda gateway=graphiti_gateway: GraphitiSearchTool(gateway),
        )
        registry.register(
            GraphitiIngestTool.SPEC,
            lambda gateway=graphiti_gateway: GraphitiIngestTool(gateway),
        )
    return registry
