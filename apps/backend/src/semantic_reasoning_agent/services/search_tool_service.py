"""Compatibility shim. Canonical implementation: ``semantic_reasoning_agent.search.tool_service``."""

from semantic_reasoning_agent.search.constants import (
    SearchToolConfigInvalidError,
    SearchToolConfigNotFoundError,
    SearchToolSystemManagedError,
    TOOL_NAME_DOCS,
    TOOL_NAME_GRAPH,
)
from semantic_reasoning_agent.search.tool_service import SearchToolConfigService

__all__ = [
    "SearchToolConfigService",
    "SearchToolConfigInvalidError",
    "SearchToolConfigNotFoundError",
    "SearchToolSystemManagedError",
    "TOOL_NAME_DOCS",
    "TOOL_NAME_GRAPH",
]
