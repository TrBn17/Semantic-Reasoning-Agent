from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from semantic_reasoning_agent.domain.contracts.evidence import CitationAnchor, Evidence, Provenance
from semantic_reasoning_agent.domain.contracts.tool_envelope import ToolMeta, ToolResult
from semantic_reasoning_agent.schemas.agent_capabilities import EvidencePolicySchema, ToolPolicySchema
from semantic_reasoning_agent.schemas.agent_profiles import AgentProfileResponse
from semantic_reasoning_agent.schemas.tasks import TaskResolveRequest
from semantic_reasoning_agent.services.task_runtime import TaskRuntimeService


def _profile(*, preset: str = "internal_qa") -> AgentProfileResponse:
    now = datetime.now(timezone.utc)
    return AgentProfileResponse(
        id="profile-1",
        workspace_id="workspace-demo",
        name="Scoped agent",
        description="",
        system_prompt="",
        allow_chat_model_override=True,
        is_default=False,
        status="active",
        capability_preset=preset,
        tool_policy=ToolPolicySchema(),
        knowledge_pack_ids=["pack-1"],
        evidence_policy=EvidencePolicySchema(allow_model_only_fallback=False),
        policy_config={
            "capability_preset": preset,
            "tool_policy": {"mode": "preset", "allowed_tools": [], "blocked_tools": []},
            "knowledge_pack_ids": ["pack-1"],
            "evidence_policy": {
                "allowed_sources": ["internal_chunk", "graph_node", "graph_edge"],
                "allow_model_only_fallback": False,
            },
        },
        task_models=[],
        tool_assignments=[
            {
                "slot": "rag",
                "tool_name": "supersearch.docs",
                "config_id": "cfg-rag",
                "enabled": True,
                "position": 0,
            }
        ],
        created_at=now,
        updated_at=now,
    )


def _tool_result(tool_name: str) -> ToolResult:
    now = datetime.now(timezone.utc)
    evidence = ()
    if tool_name == "supersearch.docs":
        evidence = (
            Evidence(
                evidence_id=uuid4(),
                source_type="internal_chunk",
                title="Allowed Doc",
                content="Pack scoped content",
                citation_anchor=CitationAnchor(anchor_type="section", label="doc", locator="doc"),
                provenance=Provenance(workspace_id="workspace-demo", captured_at=now),
                document_id="doc-allowed",
                chunk_id="chunk-1",
                section="doc",
            ),
        )
    return ToolResult(
        call_id=uuid4(),
        tool_name=tool_name,
        status="success",
        started_at=now,
        finished_at=now,
        latency_ms=0,
        evidence=evidence,
        meta=ToolMeta(),
    )


def test_internal_qa_scope_only_invokes_retrieval(monkeypatch) -> None:
    runtime: TaskRuntimeService = __import__(
        "semantic_reasoning_agent.core.container",
        fromlist=["get_app_container"],
    ).get_app_container().task_runtime_service

    calls: list[str] = []
    monkeypatch.setattr(
        runtime,
        "_resolve_workspace_and_agent_profile",
        lambda request: ("workspace-demo", _profile()),
    )
    monkeypatch.setattr(
        runtime._knowledge_pack_service,
        "resolve_document_scope",
        lambda workspace_id, knowledge_pack_ids: ["doc-allowed"],
    )

    def _invoke(envelope):
        calls.append(envelope.tool_name)
        return _tool_result(envelope.tool_name)

    monkeypatch.setattr(runtime._tool_runtime, "invoke", _invoke)

    result = runtime.resolve_request(
        TaskResolveRequest(
            content="Show the ontology graph relationship for this document.",
            workspace_id="workspace-demo",
            top_k=3,
        )
    )

    assert calls == ["supersearch.docs"]
    assert len(result.citations) == 1


def test_request_document_override_is_intersected_with_pack_scope(monkeypatch) -> None:
    runtime: TaskRuntimeService = __import__(
        "semantic_reasoning_agent.core.container",
        fromlist=["get_app_container"],
    ).get_app_container().task_runtime_service

    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        runtime,
        "_resolve_workspace_and_agent_profile",
        lambda request: ("workspace-demo", _profile()),
    )
    monkeypatch.setattr(
        runtime._knowledge_pack_service,
        "resolve_document_scope",
        lambda workspace_id, knowledge_pack_ids: ["doc-allowed"],
    )

    def _invoke(envelope):
        calls.append(dict(envelope.arguments))
        return _tool_result(envelope.tool_name)

    monkeypatch.setattr(runtime._tool_runtime, "invoke", _invoke)

    runtime.resolve_request(
        TaskResolveRequest(
            content="Explain this pack",
            workspace_id="workspace-demo",
            document_ids=["doc-allowed", "doc-blocked"],
            top_k=3,
        )
    )

    assert calls == [
        {
            "config_ref": "cfg-rag",
            "query": "Explain this pack",
            "document_ids": ["doc-allowed"],
            "top_k": 3,
        }
    ]


def test_empty_slot_assignments_do_not_trigger_implicit_tool_fallback(monkeypatch) -> None:
    runtime: TaskRuntimeService = __import__(
        "semantic_reasoning_agent.core.container",
        fromlist=["get_app_container"],
    ).get_app_container().task_runtime_service

    profile = _profile()
    profile.tool_assignments = []
    calls: list[str] = []
    monkeypatch.setattr(
        runtime,
        "_resolve_workspace_and_agent_profile",
        lambda request: ("workspace-demo", profile),
    )
    monkeypatch.setattr(
        runtime._knowledge_pack_service,
        "resolve_document_scope",
        lambda workspace_id, knowledge_pack_ids: ["doc-allowed"],
    )

    def _invoke(envelope):
        calls.append(envelope.tool_name)
        return _tool_result(envelope.tool_name)

    monkeypatch.setattr(runtime._tool_runtime, "invoke", _invoke)

    result = runtime.resolve_request(
        TaskResolveRequest(
            content="Explain this pack",
            workspace_id="workspace-demo",
            document_ids=["doc-allowed"],
            top_k=3,
        )
    )

    assert calls == []
    assert result.citations == []
