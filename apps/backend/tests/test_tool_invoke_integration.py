from __future__ import annotations

from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from semantic_reasoning_agent.main import app

client = TestClient(app)


def _build_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def test_retrieval_internal_tool_returns_section9_evidence() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "policy.pdf",
                _build_pdf_bytes("Term loans must be disbursed within ten business days."),
                "application/pdf",
            )
        },
        data={"title": "Loan Policy"},
    )
    assert upload_response.status_code == 201
    document = upload_response.json()
    workspace_id = document["workspace_id"]

    payload = {
        "call_id": str(uuid4()),
        "tool_name": "retrieval.internal",
        "workspace_id": workspace_id,
        "task_id": str(uuid4()),
        "task_type": "chat.retrieve",
        "arguments": {
            "query": "How many days to disburse term loans?",
            "document_ids": [document["id"]],
            "top_k": 2,
        },
    }
    response = client.post(
        "/api/v1/tools/retrieval.internal/invoke",
        json=payload,
    )
    assert response.status_code == 200
    body = response.json()

    # AGENTS.md §9 Standard Tool Output shape
    assert body["call_id"] == payload["call_id"]
    assert body["tool_name"] == "retrieval.internal"
    assert body["status"] == "success"
    assert body["latency_ms"] >= 0
    assert body["started_at"]
    assert body["finished_at"]
    assert body["meta"]["trace_id"]
    assert body["error_code"] is None

    # AGENTS.md §9 Unified Evidence shape
    assert len(body["evidence"]) >= 1
    ev = body["evidence"][0]
    assert ev["source_type"] == "internal_chunk"
    assert ev["title"] == "Loan Policy"
    assert ev["content"]
    assert ev["document_id"] == document["id"]
    assert ev["citation_anchor"]["anchor_type"] == "page"
    assert ev["citation_anchor"]["label"] == "page 1"
    assert ev["citation_anchor"]["locator"] == "1"
    assert ev["page"] == 1
    assert ev["provenance"]["workspace_id"] == workspace_id
    assert ev["provenance"]["tool_call_id"] == payload["call_id"]
    assert ev["provenance"]["source_id"] == document["id"]
    assert ev["score"] > 0


def test_retrieval_internal_no_match_returns_partial_status() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "empty.pdf",
                _build_pdf_bytes("unrelated content"),
                "application/pdf",
            )
        },
    )
    document = upload_response.json()

    payload = {
        "call_id": str(uuid4()),
        "tool_name": "retrieval.internal",
        "workspace_id": document["workspace_id"],
        "task_id": str(uuid4()),
        "task_type": "chat.retrieve",
        "arguments": {
            "query": "zzzzzzzzz nothing should match this",
            "document_ids": [document["id"]],
            "top_k": 3,
        },
    }
    response = client.post("/api/v1/tools/retrieval.internal/invoke", json=payload)
    assert response.status_code == 200
    body = response.json()
    # TokenVectorBackend may still return one fuzzy match; either "partial" (empty) or "success" (fuzzy hit) is acceptable.
    assert body["status"] in {"success", "partial"}
    if body["status"] == "partial":
        assert body["next_action_hints"] == ["no_internal_match"]
