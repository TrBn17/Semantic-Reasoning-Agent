from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolMeta, ToolResult
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.tools.base import Tool


_SPEC_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Episode name."},
        "episode_body": {"type": "string", "description": "Normalized text body to ingest."},
        "source_description": {"type": "string", "description": "Where the episode came from."},
    },
    "required": ["name", "episode_body", "source_description"],
    "additionalProperties": False,
}


class GraphitiIngestTool(Tool):
    tool_name = "graphiti.ingest_episode"

    SPEC = ToolSpec(
        tool_name="graphiti.ingest_episode",
        tool_family="graph",
        tool_type="internal_service",
        version="1.0.0",
        description="Ingests a normalized episode into the Graphiti runtime graph.",
        input_schema=_SPEC_INPUT_SCHEMA,
        input_schema_ref="srag:graphiti.ingest_episode.in.v1",
        capabilities=("graph_write", "episode_ingest"),
        risk_level="medium",
        side_effect_level="write_internal",
        supports_parallel=False,
        timeout_ms=15000,
    )

    def __init__(self, gateway: GraphitiGateway) -> None:
        self._gateway = gateway

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        arguments = envelope.arguments if isinstance(envelope.arguments, dict) else {}
        name = arguments.get("name")
        episode_body = arguments.get("episode_body")
        source_description = arguments.get("source_description")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("graphiti.ingest_episode requires a non-empty 'name' argument.")
        if not isinstance(episode_body, str) or not episode_body.strip():
            raise ValueError("graphiti.ingest_episode requires a non-empty 'episode_body' argument.")
        if not isinstance(source_description, str) or not source_description.strip():
            raise ValueError("graphiti.ingest_episode requires a non-empty 'source_description' argument.")

        now = datetime.now(timezone.utc)
        if not self._gateway.is_enabled():
            return ToolResult(
                call_id=envelope.call_id,
                tool_name=self.tool_name,
                status="partial",
                started_at=now,
                finished_at=now,
                latency_ms=0,
                next_action_hints=("graphiti_disabled",),
                meta=ToolMeta(provider="graphiti"),
            )

        artifact = self._gateway.ingest_episode(
            name=name,
            episode_body=episode_body,
            source_description=source_description,
            workspace_id=envelope.workspace_id,
        )
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status="success",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            artifacts=(artifact,),
            meta=ToolMeta(provider="graphiti"),
        )
