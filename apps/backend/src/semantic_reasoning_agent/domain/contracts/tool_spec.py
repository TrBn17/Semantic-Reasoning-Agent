from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

ToolFamily = Literal[
    "document",
    "retrieval",
    "ontology",
    "graph",
    "web",
    "mcp",
    "artifact",
    "admin",
]

ToolType = Literal["internal_service", "external_adapter", "worker_job"]

RiskLevel = Literal["low", "medium", "high"]

SideEffectLevel = Literal["read_only", "write_internal", "write_external"]

WorkspaceScope = Literal["workspace", "global"]

_RISK_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class ToolSpec:
    """Tool Registry Model — AGENTS.md §9.

    A declarative description of a registered tool. ``input_schema`` is the
    actual JSON Schema dict sent to the LLM for native function calling;
    ``input_schema_ref`` / ``output_schema_ref`` are stable identifier strings
    used for audit and schema versioning.
    """

    tool_name: str
    tool_family: ToolFamily
    tool_type: ToolType
    version: str
    description: str
    input_schema: Mapping[str, Any]
    input_schema_ref: str = ""
    output_schema_ref: str = "srag:tool.out.v1"
    capabilities: tuple[str, ...] = ()
    risk_level: RiskLevel = "low"
    side_effect_level: SideEffectLevel = "read_only"
    supports_parallel: bool = True
    supports_streaming: bool = False
    requires_confirmation: bool = False
    timeout_ms: int = 15000
    workspace_scope: WorkspaceScope = "workspace"

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Serialize to the Anthropic Messages API ``tools`` entry shape."""
        return {
            "name": self.tool_name,
            "description": self.description,
            "input_schema": dict(self.input_schema),
        }

    def to_openai_tool(self) -> dict[str, Any]:
        """Serialize to the OpenAI Chat Completions ``tools`` entry shape."""
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.description,
                "parameters": dict(self.input_schema),
            },
        }


def risk_at_most(candidate: RiskLevel, ceiling: RiskLevel) -> bool:
    return _RISK_ORDER[candidate] <= _RISK_ORDER[ceiling]
