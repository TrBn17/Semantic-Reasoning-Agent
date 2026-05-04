"""Compatibility shim. Canonical implementation: ``semantic_reasoning_agent.agents.builtin_context``."""

from semantic_reasoning_agent.agents.builtin_context import (
    BuiltinAgentContextService,
    MEMORY_BODY_MAX_CHARS,
    NOTE_MAX_CHARS,
    read_packaged_file,
)

__all__ = [
    "BuiltinAgentContextService",
    "MEMORY_BODY_MAX_CHARS",
    "NOTE_MAX_CHARS",
    "read_packaged_file",
]
