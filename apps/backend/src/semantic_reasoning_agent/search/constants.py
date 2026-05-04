"""Constants and shared exceptions for supersearch (SearchToolConfigService)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

TOOL_NAME_DOCS = "supersearch.docs"
TOOL_NAME_GRAPH = "supersearch.graph"
RouteDecision = Literal["graph", "sql_facts", "hybrid"]


class SearchToolConfigNotFoundError(LookupError):
    """Raised when a config id cannot be resolved for the current workspace."""


class SearchToolConfigInvalidError(ValueError):
    """Raised when a create/update payload fails cross-field validation."""


class SearchToolSystemManagedError(ValueError):
    """Raised when a system-managed config cannot be directly mutated."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_DOCS_SYSTEM_KEY = "workspace_default_rag"
DEFAULT_GRAPH_SYSTEM_KEY = "workspace_default_ontology_search"
FORCED_EMBEDDING_PROVIDER = "cloudflare"
FORCED_EMBEDDING_MODEL = "bge-m3"
