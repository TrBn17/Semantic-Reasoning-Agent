from __future__ import annotations

from dataclasses import dataclass

from semantic_reasoning_agent.schemas.agent_capabilities import (
    AgentCapabilityCatalogResponse,
    AgentCapabilityConfigSchema,
    AgentCapabilityPresetSchema,
    AgentCapabilityToolSchema,
    EvidencePolicySchema,
    ToolPolicySchema,
)
from semantic_reasoning_agent.services.tool_registry import ToolRegistry


POLICY_CONFIG_CAPABILITY_KEYS = {
    "capability_preset",
    "tool_policy",
    "knowledge_pack_ids",
    "evidence_policy",
}


@dataclass(frozen=True)
class CapabilityPreset:
    preset: str
    label: str
    description: str
    allowed_tool_families: tuple[str, ...]
    default_tool_order: tuple[str, ...]
    ontology_enabled: bool = False
    graph_enabled: bool = False
    external_tools_allowed: bool = False


CAPABILITY_PRESETS: dict[str, CapabilityPreset] = {
    "internal_qa": CapabilityPreset(
        preset="internal_qa",
        label="Internal Q&A",
        description="Uses indexed workspace documents for grounded answers.",
        allowed_tool_families=("retrieval",),
        default_tool_order=("retrieval.internal",),
    ),
    "ontology_curator": CapabilityPreset(
        preset="ontology_curator",
        label="Ontology Curator",
        description="Combines document retrieval with ontology lookup for curation tasks.",
        allowed_tool_families=("retrieval", "ontology"),
        default_tool_order=("retrieval.internal", "ontology.lookup"),
        ontology_enabled=True,
    ),
    "graph_explorer": CapabilityPreset(
        preset="graph_explorer",
        label="Graph Explorer",
        description="Combines document retrieval with runtime graph search.",
        allowed_tool_families=("retrieval", "graph"),
        default_tool_order=("retrieval.internal", "graphiti.search"),
        graph_enabled=True,
    ),
    "document_analyst": CapabilityPreset(
        preset="document_analyst",
        label="Document Analyst",
        description="Broad internal analysis across documents, ontology, and graph context.",
        allowed_tool_families=("retrieval", "ontology", "graph"),
        default_tool_order=("retrieval.internal", "ontology.lookup", "graphiti.search"),
        ontology_enabled=True,
        graph_enabled=True,
    ),
}


def default_capability_config() -> AgentCapabilityConfigSchema:
    return AgentCapabilityConfigSchema()


def resolve_capability_config(policy_config: dict | None) -> AgentCapabilityConfigSchema:
    raw = dict(policy_config or {})
    return AgentCapabilityConfigSchema(
        capability_preset=str(raw.get("capability_preset") or "internal_qa"),
        tool_policy=ToolPolicySchema.model_validate(raw.get("tool_policy") or {}),
        knowledge_pack_ids=[str(item) for item in (raw.get("knowledge_pack_ids") or []) if item],
        evidence_policy=EvidencePolicySchema.model_validate(raw.get("evidence_policy") or {}),
    )


def has_explicit_capability_config(policy_config: dict | None) -> bool:
    raw = dict(policy_config or {})
    return any(key in raw for key in POLICY_CONFIG_CAPABILITY_KEYS)


def merge_policy_config(
    base: dict | None,
    *,
    capability_preset: str | None = None,
    tool_policy: ToolPolicySchema | None = None,
    knowledge_pack_ids: list[str] | None = None,
    evidence_policy: EvidencePolicySchema | None = None,
) -> dict:
    merged = dict(base or {})
    if capability_preset is not None:
        merged["capability_preset"] = capability_preset
    if tool_policy is not None:
        merged["tool_policy"] = tool_policy.model_dump()
    if knowledge_pack_ids is not None:
        merged["knowledge_pack_ids"] = list(knowledge_pack_ids)
    if evidence_policy is not None:
        merged["evidence_policy"] = evidence_policy.model_dump()
    return merged


class AgentCapabilityService:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    def list_presets(self) -> list[AgentCapabilityPresetSchema]:
        return [
            AgentCapabilityPresetSchema(
                preset=preset.preset,
                label=preset.label,
                description=preset.description,
                allowed_tool_families=list(preset.allowed_tool_families),
                default_tool_order=list(preset.default_tool_order),
                ontology_enabled=preset.ontology_enabled,
                graph_enabled=preset.graph_enabled,
                external_tools_allowed=preset.external_tools_allowed,
            )
            for preset in CAPABILITY_PRESETS.values()
        ]

    def list_user_facing_tools(self) -> list[AgentCapabilityToolSchema]:
        tools = [
            AgentCapabilityToolSchema(
                tool_name=spec.tool_name,
                label=_tool_label(spec.tool_name),
                family=spec.tool_family,
                description=spec.description,
                risk_level=spec.risk_level,
                requires_confirmation=spec.requires_confirmation,
            )
            for spec in self._tool_registry.list()
        ]
        tools.sort(key=lambda item: (item.family, item.label.lower()))
        return tools

    def catalog(self) -> AgentCapabilityCatalogResponse:
        grouped: dict[str, list[dict[str, str]]] = {}
        for tool in self.list_user_facing_tools():
            grouped.setdefault(tool.family, []).append(
                {
                    "tool_name": tool.tool_name,
                    "label": tool.label,
                    "description": tool.description,
                }
            )
        return AgentCapabilityCatalogResponse(
            presets=self.list_presets(),
            tool_families=grouped,
        )


def get_capability_preset(name: str | None) -> CapabilityPreset:
    if name and name in CAPABILITY_PRESETS:
        return CAPABILITY_PRESETS[name]
    return CAPABILITY_PRESETS["internal_qa"]


def _tool_label(tool_name: str) -> str:
    if tool_name == "retrieval.internal":
        return "Internal Retrieval"
    if tool_name == "ontology.lookup":
        return "Ontology Lookup"
    if tool_name == "graphiti.search":
        return "Graph Search"
    return tool_name.replace(".", " ").title()
