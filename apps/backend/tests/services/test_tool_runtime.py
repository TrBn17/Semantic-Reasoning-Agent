from __future__ import annotations

import time
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import (
    CitationAnchor,
    Evidence,
    Provenance,
)
from semantic_reasoning_agent.domain.contracts.tool_envelope import (
    ToolEnvelope,
    ToolMeta,
    ToolResult,
)
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.services.tool_registry import ToolRegistry
from semantic_reasoning_agent.services.tool_runtime import ToolRuntime
from semantic_reasoning_agent.tools.base import Tool


def _spec(
    name: str = "test.tool",
    *,
    timeout_ms: int = 15000,
    requires_confirmation: bool = False,
) -> ToolSpec:
    return ToolSpec(
        tool_name=name,
        tool_family="retrieval",
        tool_type="internal_service",
        version="1.0.0",
        description="test",
        input_schema={"type": "object"},
        timeout_ms=timeout_ms,
        requires_confirmation=requires_confirmation,
    )


def _envelope(tool_name: str = "test.tool", *, timeout_ms: int = 15000) -> ToolEnvelope:
    from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolConstraints

    return ToolEnvelope(
        call_id=uuid4(),
        tool_name=tool_name,
        workspace_id="workspace-demo",
        task_id=str(uuid4()),
        task_type="chat.retrieve",
        constraints=ToolConstraints(timeout_ms=timeout_ms),
    )


class _EchoTool(Tool):
    tool_name = "test.tool"

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        anchor = CitationAnchor(anchor_type="page", label="page 1", locator="1")
        provenance = Provenance(workspace_id=envelope.workspace_id, captured_at=now)
        evidence = Evidence(
            evidence_id=uuid4(),
            source_type="internal_chunk",
            title="t",
            content="c",
            citation_anchor=anchor,
            provenance=provenance,
        )
        return ToolResult(
            call_id=envelope.call_id,
            tool_name=self.tool_name,
            status="success",
            started_at=now,
            finished_at=now,
            latency_ms=0,
            evidence=(evidence,),
        )


class _BoomTool(Tool):
    tool_name = "test.tool"

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        raise RuntimeError("boom from inside the tool")


class _SleepyTool(Tool):
    tool_name = "test.tool"

    def run(self, envelope: ToolEnvelope) -> ToolResult:
        time.sleep(0.5)
        raise AssertionError("should have timed out")


def test_unknown_tool_returns_failed_result() -> None:
    runtime = ToolRuntime(ToolRegistry())
    envelope = _envelope(tool_name="missing")
    result = runtime.invoke(envelope)
    assert result.status == "failed"
    assert result.error_code == "unknown_tool"
    assert result.call_id == envelope.call_id
    assert result.tool_name == "missing"


def test_confirmation_required_blocks_invocation() -> None:
    registry = ToolRegistry()
    registry.register(_spec(requires_confirmation=True), _EchoTool)
    runtime = ToolRuntime(registry)
    result = runtime.invoke(_envelope())
    assert result.status == "failed"
    assert result.error_code == "confirmation_required"


def test_exception_caught_and_wrapped() -> None:
    registry = ToolRegistry()
    registry.register(_spec(), _BoomTool)
    runtime = ToolRuntime(registry)
    result = runtime.invoke(_envelope())
    assert result.status == "failed"
    assert result.error_code == "tool_exception"
    assert "boom from inside the tool" in (result.error_message or "")
    assert result.meta.trace_id is not None


def test_timeout_returns_failed_result() -> None:
    registry = ToolRegistry()
    # Spec timeout 100ms, constraints timeout 100ms — SleepyTool sleeps 500ms.
    registry.register(_spec(timeout_ms=100), _SleepyTool)
    runtime = ToolRuntime(registry)
    result = runtime.invoke(_envelope(timeout_ms=100))
    assert result.status == "failed"
    assert result.error_code == "timeout"


def test_successful_invoke_populates_metadata_and_latency() -> None:
    registry = ToolRegistry()
    registry.register(_spec(), _EchoTool)
    runtime = ToolRuntime(registry)
    envelope = _envelope()
    result = runtime.invoke(envelope)
    assert result.status == "success"
    assert result.call_id == envelope.call_id
    assert result.latency_ms >= 0
    assert result.meta.trace_id is not None
    assert len(result.evidence) == 1


def test_invoke_parallel_returns_result_per_envelope() -> None:
    registry = ToolRegistry()
    registry.register(_spec(), _EchoTool)
    runtime = ToolRuntime(registry)
    envelopes = [_envelope(), _envelope(), _envelope()]
    results = runtime.invoke_parallel(envelopes)
    assert len(results) == 3
    assert [r.status for r in results] == ["success", "success", "success"]
    assert {r.call_id for r in results} == {e.call_id for e in envelopes}
