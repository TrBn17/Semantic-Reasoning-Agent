from __future__ import annotations

from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app


def test_list_tools_returns_registered_phase3_tools() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    body = response.json()
    tool_names = {entry["tool_name"] for entry in body}
    assert {"retrieval.internal", "ontology.lookup"}.issubset(tool_names)

    retrieval = next(e for e in body if e["tool_name"] == "retrieval.internal")
    assert retrieval["tool_family"] == "retrieval"
    assert retrieval["risk_level"] == "low"
    assert retrieval["side_effect_level"] == "read_only"
    assert "query" in retrieval["input_schema"]["properties"]


def test_list_tools_filters_by_family() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/tools", params={"family": "ontology"})
    assert response.status_code == 200
    body = response.json()
    assert all(item["tool_family"] == "ontology" for item in body)
    assert any(item["tool_name"] == "ontology.lookup" for item in body)


_CALL_ID = "11111111-1111-1111-1111-111111111111"


def _invoke_payload(tool_name: str, arguments: dict) -> dict:
    return {
        "call_id": _CALL_ID,
        "tool_name": tool_name,
        "workspace_id": "workspace-demo",
        "task_id": "task-demo",
        "task_type": "chat.retrieve",
        "arguments": arguments,
    }


def test_invoke_unknown_tool_returns_404() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/tools/does.not.exist/invoke",
        json=_invoke_payload("does.not.exist", {}),
    )
    assert response.status_code == 404


def test_invoke_mismatched_path_and_body_tool_name_returns_400() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/tools/ontology.lookup/invoke",
        json=_invoke_payload("retrieval.internal", {"query": "anything"}),
    )
    assert response.status_code == 400


def test_invoke_retrieval_internal_without_query_returns_failed() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/tools/retrieval.internal/invoke",
        json=_invoke_payload("retrieval.internal", {}),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_code"] == "tool_exception"
    assert "query" in (body["error_message"] or "").lower()


def test_invoke_ontology_lookup_without_published_ontology_returns_partial() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/tools/ontology.lookup/invoke",
        json=_invoke_payload("ontology.lookup", {"mode": "published_graph"}),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["next_action_hints"] == ["no_published_ontology"]
    assert body["evidence"] == []
    assert body["meta"]["trace_id"]
    assert body["call_id"] == _CALL_ID
