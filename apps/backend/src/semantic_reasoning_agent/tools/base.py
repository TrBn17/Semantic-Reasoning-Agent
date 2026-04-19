from __future__ import annotations

from abc import ABC, abstractmethod

from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolResult


class Tool(ABC):
    """Atomic execution unit.

    Each Tool advertises a stable `tool_id` and consumes a ToolEnvelope
    whose `inputs` mapping carries the tool-specific arguments. The
    returned ToolResult must be JSON-serializable.
    """

    tool_id: str

    @abstractmethod
    def run(self, envelope: ToolEnvelope) -> ToolResult: ...
