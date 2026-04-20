from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Mapping
from uuid import UUID

from semantic_reasoning_agent.domain.contracts.evidence import Evidence

ToolStatus = Literal["success", "partial", "failed"]


@dataclass(frozen=True)
class OntologyContextRef:
    """Compact ontology snapshot attached to a tool call — AGENTS.md §9.

    Distinct from ``domain.contracts.ontology_context.OntologyContext`` (the
    full emergent schema used by extractors). Tools only need grounding hints:
    a detected domain string and best-effort entity/relation type hints. Empty
    tuples are valid — no hardcoded defaults (LLM-first).
    """

    domain: str | None = None
    entity_hints: tuple[str, ...] = ()
    relation_hints: tuple[str, ...] = ()
    normalization_rules: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class ToolConstraints:
    """Runtime constraints carried per tool call — AGENTS.md §9."""

    web_enabled: bool = False
    freshness_required: bool = False
    max_results: int = 10
    timeout_ms: int = 15000


@dataclass(frozen=True)
class ToolEnvelope:
    """Standard Tool Input — AGENTS.md §9.

    Every tool invocation flows through this envelope. ``call_id`` is the
    runtime-assigned UUID for trace/audit; ``tool_name`` must match a
    registered ``ToolSpec.tool_name``.
    """

    call_id: UUID
    tool_name: str
    workspace_id: str
    task_id: str
    task_type: str
    task_payload: Mapping[str, Any] = field(default_factory=dict)
    ontology_context: OntologyContextRef = field(default_factory=OntologyContextRef)
    arguments: Mapping[str, Any] = field(default_factory=dict)
    constraints: ToolConstraints = field(default_factory=ToolConstraints)
    workflow_id: str | None = None


@dataclass(frozen=True)
class ToolMeta:
    """Execution metadata captured by the runtime — AGENTS.md §9."""

    provider: str | None = None
    provider_version: str | None = None
    trace_id: str | None = None


@dataclass(frozen=True)
class ToolResult:
    """Standard Tool Output — AGENTS.md §9.

    The runtime always populates ``call_id, tool_name, status, started_at,
    finished_at, latency_ms`` — tools only need to return evidence, artifacts,
    state_patch, and hints (or raise, in which case the runtime constructs a
    failed result).
    """

    call_id: UUID
    tool_name: str
    status: ToolStatus
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    evidence: tuple[Evidence, ...] = ()
    artifacts: tuple[Mapping[str, Any], ...] = ()
    state_patch: Mapping[str, Any] = field(default_factory=dict)
    next_action_hints: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None
    meta: ToolMeta = field(default_factory=ToolMeta)
