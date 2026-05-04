from __future__ import annotations

import uuid
from typing import Literal, TypedDict, TypeGuard

BuiltinAgentRole = Literal["orchestrator", "graph", "docs"]

BUILTIN_AGENT_ROLES: tuple[BuiltinAgentRole, ...] = ("orchestrator", "graph", "docs")

# Stable deterministic UUID namespace for workspace built-in agent *profiles* (CRUD lists).
_BUILTIN_AGENT_PROFILE_NAMESPACE = uuid.UUID("a7352c91-9c2e-5f91-bcff-4e8cf4b2c631")


class BuiltinAgentSeedLabels(TypedDict):
    name: str
    description: str


BUILTIN_AGENT_PROFILE_SEED: dict[BuiltinAgentRole, BuiltinAgentSeedLabels] = {
    "orchestrator": {
        "name": "Orchestrator",
        "description": (
            "Chat-facing task agent: grounding, tools, ontology, and orchestration presets for workspace tasks."
        ),
    },
    "graph": {
        "name": "Graph specialist",
        "description": "Graph and ontology-grounded retrieval specialist (LlamaIndex ReAct sub-agent context).",
    },
    "docs": {
        "name": "Docs specialist",
        "description": "Document RAG retrieval specialist (LlamaIndex ReAct sub-agent context).",
    },
}


def builtin_agent_profile_id(workspace_id: str, role: BuiltinAgentRole) -> str:
    """Deterministic agent profile primary key per (workspace, built-in role)."""
    return str(uuid.uuid5(_BUILTIN_AGENT_PROFILE_NAMESPACE, f"{workspace_id}\xff{role}"))


def is_builtin_agent_role(value: str) -> TypeGuard[BuiltinAgentRole]:
    return value in BUILTIN_AGENT_ROLES
