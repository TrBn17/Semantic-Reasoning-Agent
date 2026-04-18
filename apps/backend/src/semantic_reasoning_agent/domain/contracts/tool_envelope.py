from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping
from uuid import UUID

ToolStatus = Literal["ok", "error", "skipped"]


@dataclass(frozen=True)
class ToolEnvelope:
    tool_id: str
    inputs: Mapping[str, Any]
    workflow_run_id: UUID | None = None
    workspace_id: UUID | None = None
    timeout_s: float = 60.0
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    tool_id: str
    status: ToolStatus
    outputs: Mapping[str, Any]
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
