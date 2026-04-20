from __future__ import annotations

import pytest

from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolEnvelope, ToolResult
from semantic_reasoning_agent.domain.contracts.tool_spec import ToolSpec
from semantic_reasoning_agent.services.tool_registry import (
    DuplicateToolError,
    ToolRegistry,
    UnknownToolError,
    build_tool_registry,
)
from semantic_reasoning_agent.tools.base import Tool


class _NoopTool(Tool):
    tool_name = "unused"

    def run(self, envelope: ToolEnvelope) -> ToolResult:  # pragma: no cover - not exercised
        raise NotImplementedError


def _spec(
    name: str,
    *,
    family: str = "retrieval",
    risk: str = "low",
) -> ToolSpec:
    return ToolSpec(
        tool_name=name,
        tool_family=family,  # type: ignore[arg-type]
        tool_type="internal_service",
        version="1.0.0",
        description=f"spec {name}",
        input_schema={"type": "object"},
        risk_level=risk,  # type: ignore[arg-type]
    )


def test_empty_registry_lists_nothing() -> None:
    registry = build_tool_registry()
    assert registry.list() == []


def test_register_and_get_spec() -> None:
    registry = ToolRegistry()
    spec = _spec("retrieval.internal")
    registry.register(spec, _NoopTool)
    assert registry.spec("retrieval.internal") == spec
    assert registry.spec("missing") is None


def test_get_instantiates_lazily_and_caches() -> None:
    registry = ToolRegistry()
    calls: list[int] = []

    def factory() -> Tool:
        calls.append(1)
        return _NoopTool()

    registry.register(_spec("x"), factory)
    first = registry.get("x")
    second = registry.get("x")
    assert first is second
    assert len(calls) == 1


def test_require_raises_on_unknown() -> None:
    registry = ToolRegistry()
    with pytest.raises(UnknownToolError):
        registry.require("nope")


def test_duplicate_registration_rejected() -> None:
    registry = ToolRegistry()
    registry.register(_spec("x"), _NoopTool)
    with pytest.raises(DuplicateToolError):
        registry.register(_spec("x"), _NoopTool)


def test_list_filters_by_family_and_risk() -> None:
    registry = ToolRegistry()
    registry.register(_spec("retrieval.internal", family="retrieval", risk="low"), _NoopTool)
    registry.register(_spec("web.extract", family="web", risk="medium"), _NoopTool)
    registry.register(_spec("graph.publish", family="graph", risk="high"), _NoopTool)

    retrieval_only = registry.list(family="retrieval")
    assert [s.tool_name for s in retrieval_only] == ["retrieval.internal"]

    low_only = registry.list(max_risk="low")
    assert [s.tool_name for s in low_only] == ["retrieval.internal"]

    low_or_medium = registry.list(max_risk="medium")
    assert {s.tool_name for s in low_or_medium} == {"retrieval.internal", "web.extract"}

    all_sorted = registry.list()
    assert [s.tool_name for s in all_sorted] == [
        "graph.publish",
        "retrieval.internal",
        "web.extract",
    ]
