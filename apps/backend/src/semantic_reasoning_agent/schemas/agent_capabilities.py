from pydantic import BaseModel, Field


class ToolPolicySchema(BaseModel):
    mode: str = "preset"
    allowed_tools: list[str] = Field(default_factory=list)
    blocked_tools: list[str] = Field(default_factory=list)


class EvidencePolicySchema(BaseModel):
    allowed_sources: list[str] = Field(
        default_factory=lambda: ["internal_chunk", "graph_node", "graph_edge"]
    )
    allow_model_only_fallback: bool = True


class AgentCapabilityConfigSchema(BaseModel):
    capability_preset: str = "internal_qa"
    tool_policy: ToolPolicySchema = Field(default_factory=ToolPolicySchema)
    knowledge_pack_ids: list[str] = Field(default_factory=list)
    evidence_policy: EvidencePolicySchema = Field(default_factory=EvidencePolicySchema)


class AgentCapabilityPresetSchema(BaseModel):
    preset: str
    label: str
    description: str
    allowed_tool_families: list[str] = Field(default_factory=list)
    default_tool_order: list[str] = Field(default_factory=list)
    ontology_enabled: bool = False
    graph_enabled: bool = False
    external_tools_allowed: bool = False


class AgentCapabilityCatalogResponse(BaseModel):
    presets: list[AgentCapabilityPresetSchema] = Field(default_factory=list)
    tool_families: dict[str, list[dict[str, str]]] = Field(default_factory=dict)


class AgentCapabilityToolSchema(BaseModel):
    tool_name: str
    label: str
    family: str
    description: str
    risk_level: str
    requires_confirmation: bool
