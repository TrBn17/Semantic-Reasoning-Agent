from __future__ import annotations

from dataclasses import dataclass

WORKFLOW_TASK_RESOLVE_CHAT = "task.resolve.chat"

TOOL_RETRIEVAL_INTERNAL = "retrieval.internal"
TOOL_ONTOLOGY_LOOKUP = "ontology.lookup"
TOOL_GRAPHITI_SEARCH = "graphiti.search"
TOOL_GRAPHITI_INGEST = "graphiti.ingest_episode"

DEFAULT_TASK_TOP_K = 3
DEFAULT_TOOL_TIMEOUT_MS = 15000
GRAPH_TOOL_TIMEOUT_MS = 10000

NO_CONTEXT_MESSAGE = "No indexed document or graph context matched that question."

ONTOLOGY_DOMAIN_WORKSPACE = "workspace_ontology"
GRAPH_DOMAIN_WORKSPACE = "workspace_runtime_graph"

ONTOLOGY_KEYWORDS: tuple[str, ...] = (
    "ontology",
    "entity",
    "entities",
    "type",
    "taxonomy",
    "schema",
)

GRAPH_KEYWORDS: tuple[str, ...] = (
    "graph",
    "relationship",
    "related",
    "connected",
    "dependency",
    "depends on",
)


@dataclass(frozen=True)
class RuntimeDefaults:
    top_k: int = DEFAULT_TASK_TOP_K
    tool_timeout_ms: int = DEFAULT_TOOL_TIMEOUT_MS
