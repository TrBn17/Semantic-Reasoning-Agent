from __future__ import annotations

from abc import ABC, abstractmethod

from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolResult


class Tool(ABC):
    """Atomic execution unit — AGENTS.md §9.

    A Tool implementation pairs with a ``ToolSpec`` (metadata) and consumes a
    ``ToolEnvelope`` whose ``arguments`` map satisfies the spec's ``input_schema``.
    The returned ``ToolResult`` must be constructed by the tool or, on exception,
    by the ``ToolRuntime`` wrapper. Tools never block on I/O without honoring the
    envelope's ``constraints.timeout_ms`` (the runtime enforces this).
    """

    tool_name: str

    @abstractmethod
    def run(self, envelope: ToolEnvelope) -> ToolResult: ...
