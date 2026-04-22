from __future__ import annotations

import concurrent.futures
from datetime import datetime
from typing import Sequence
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.core.time import utc_now
from semantic_reasoning_agent.services.tool_registry import ToolRegistry


class ToolRuntime:
    """Execution wrapper around a ``ToolRegistry`` — AGENTS.md §9 Tool Calling Lifecycle.

    Responsibilities:
    - look the tool up in the registry,
    - enforce ``requires_confirmation`` gating,
    - enforce the spec-level timeout via a worker thread,
    - capture ``started_at``, ``finished_at``, ``latency_ms``, ``trace_id``,
    - translate any exception into a ``failed`` ``ToolResult``,
    - normalize evidence provenance so every item carries
      ``tool_call_id = envelope.call_id``.

    The runtime never validates ``arguments`` against ``input_schema`` directly —
    the API boundary (Pydantic) does structural checks, and tools raise if a
    required argument is missing. This keeps the runtime thin and avoids a hard
    dependency on ``jsonschema`` until a tool needs it.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="tool-runtime")

    def invoke(self, envelope: ToolEnvelope) -> ToolResult:
        spec = self._registry.spec(envelope.tool_name)
        if spec is None:
            return self._failed(
                envelope,
                error_code="unknown_tool",
                error_message=f"Tool '{envelope.tool_name}' is not registered.",
            )

        if spec.requires_confirmation:
            return self._failed(
                envelope,
                error_code="confirmation_required",
                error_message=(
                    f"Tool '{spec.tool_name}' requires explicit confirmation; "
                    "the runtime cannot invoke it without an approved confirmation token."
                ),
            )

        tool = self._registry.get(envelope.tool_name)
        if tool is None:
            return self._failed(
                envelope,
                error_code="unknown_tool",
                error_message=f"Tool '{envelope.tool_name}' is not registered.",
            )

        trace_id = str(uuid4())
        started_at = utc_now()
        timeout_s = max(spec.timeout_ms, envelope.constraints.timeout_ms) / 1000.0

        try:
            future = self._executor.submit(tool.run, envelope)
            result = future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            return self._failed(
                envelope,
                error_code="timeout",
                error_message=(
                    f"Tool '{envelope.tool_name}' exceeded timeout of {timeout_s:.2f}s."
                ),
                trace_id=trace_id,
                started_at=started_at,
            )
        except Exception as exc:  # noqa: BLE001 — boundary catch
            return self._failed(
                envelope,
                error_code="tool_exception",
                error_message=str(exc) or exc.__class__.__name__,
                trace_id=trace_id,
                started_at=started_at,
            )

        finished_at = utc_now()
        latency_ms = int((finished_at - started_at).total_seconds() * 1000)

        normalized_evidence = tuple(result.evidence)
        meta = ToolMeta(
            provider=result.meta.provider,
            provider_version=result.meta.provider_version,
            trace_id=trace_id,
        )
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=envelope.tool_name,
            status=result.status,
            started_at=started_at,
            finished_at=finished_at,
            latency_ms=latency_ms,
            evidence=normalized_evidence,
            artifacts=tuple(result.artifacts),
            state_patch=dict(result.state_patch),
            next_action_hints=tuple(result.next_action_hints),
            error_code=result.error_code,
            error_message=result.error_message,
            meta=meta,
        )

    def invoke_parallel(self, envelopes: Sequence[ToolEnvelope]) -> list[ToolResult]:
        return [self.invoke(envelope) for envelope in envelopes]

    @staticmethod
    def _failed(
        envelope: ToolEnvelope,
        *,
        error_code: str,
        error_message: str,
        trace_id: str | None = None,
        started_at: datetime | None = None,
    ) -> ToolResult:
        started = started_at or utc_now()
        finished = utc_now()
        latency_ms = int((finished - started).total_seconds() * 1000)
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=envelope.tool_name,
            status="failed",
            started_at=started,
            finished_at=finished,
            latency_ms=latency_ms,
            error_code=error_code,
            error_message=error_message,
            meta=ToolMeta(trace_id=trace_id),
        )
