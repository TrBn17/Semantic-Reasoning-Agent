"""Integration tests for the supersearch.docs / supersearch.graph pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.main import app
from semantic_reasoning_agent.persistence.models import DocumentChunkORM, DocumentORM
from semantic_reasoning_agent.services.bm25_scorer import BM25Scorer
from semantic_reasoning_agent.services.search_tool_service import (
    SearchToolConfigInvalidError,
    SearchToolConfigNotFoundError,
    SearchToolConfigService,
)


WORKSPACE_ID = "workspace-demo"


def _seed_document_chunks(count: int = 3) -> list[str]:
    """Insert a small document + chunks and return chunk_ids."""

    container = get_app_container()
    now = datetime.now(timezone.utc)
    chunk_ids: list[str] = []
    with container.database_manager.session() as session:
        document = DocumentORM(
            id="doc-bm25",
            workspace_id=WORKSPACE_ID,
            title="BM25 sample",
            filename="sample.txt",
            document_type="txt",
            status="indexed",
            parser_version="test",
            source_url="",
            binary_content=b"",
            tags=[],
            ingestion_options={},
            created_at=now,
            updated_at=now,
        )
        session.add(document)
        session.flush()

        chunks = [
            ("c1", "Alpha initiative depends on beta system for approvals."),
            ("c2", "Audit service traces every beta system event."),
            ("c3", "Completely unrelated cooking instructions for a cake."),
        ][:count]
        for order, (cid, text) in enumerate(chunks):
            session.add(
                DocumentChunkORM(
                    chunk_id=cid,
                    document_id=document.id,
                    workspace_id=WORKSPACE_ID,
                    document_title=document.title,
                    document_type=document.document_type,
                    text=text,
                    chunk_index=order,
                    source_url="",
                    parser_version="test",
                    embedding={},
                    created_at=now,
                )
            )
            chunk_ids.append(cid)
    return chunk_ids


# ------------------ BM25 scorer unit tests ------------------


def test_bm25_scorer_orders_exact_matches_first() -> None:
    scorer = BM25Scorer(
        [
            ("a", "alpha depends on beta system for approvals"),
            ("b", "audit service observes beta system events"),
            ("c", "completely unrelated cooking"),
        ]
    )
    hits = scorer.score("beta system", top_k=3)
    top_ids = [hit.chunk_id for hit in hits[:2]]
    assert set(top_ids) == {"a", "b"}
    assert all(hit.chunk_id != "c" for hit in hits)


def test_bm25_scorer_empty_query_returns_empty() -> None:
    scorer = BM25Scorer([("x", "some text")])
    assert scorer.score("   ", top_k=5) == []
    assert scorer.score("", top_k=5) == []


def test_bm25_scorer_handles_empty_corpus() -> None:
    assert BM25Scorer([]).score("anything", top_k=5) == []


# ------------------ Service-level CRUD + validation ------------------


def _service() -> SearchToolConfigService:
    return get_app_container().search_tool_service


def test_service_create_docs_config_requires_document_ids_when_scoped() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import SearchToolConfigCreateRequest

    with pytest.raises(SearchToolConfigInvalidError):
        svc.create(
            SearchToolConfigCreateRequest(
                tool_type="docs",
                name="bad",
                provider="openai",
                model="gpt-4o-mini",
                collection_target="documents",
                document_ids=[],
            )
        )


def test_service_create_graph_config_requires_version_id_when_scoped() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import SearchToolConfigCreateRequest

    with pytest.raises(SearchToolConfigInvalidError):
        svc.create(
            SearchToolConfigCreateRequest(
                tool_type="graph",
                name="bad-graph",
                provider="openai",
                model="gpt-4o-mini",
                ontology_scope="version",
                ontology_version_id=None,
            )
        )


def test_service_rejects_duplicate_names_within_tool_type() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import SearchToolConfigCreateRequest

    payload = SearchToolConfigCreateRequest(
        tool_type="docs",
        name="my-docs",
        provider="openai",
        model="gpt-4o-mini",
    )
    first = svc.create(payload)
    assert first.id

    with pytest.raises(SearchToolConfigInvalidError):
        svc.create(payload)

    # Same name under graph tool_type is allowed.
    svc.create(payload.model_copy(update={"tool_type": "graph"}))


def test_service_readiness_reflects_model_config() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import SearchToolConfigCreateRequest

    created = svc.create(
        SearchToolConfigCreateRequest(
            tool_type="docs",
            name="unready",
            provider="never-configured-provider",
            model="nope",
        )
    )
    assert created.ready is False
    assert "not ready" in created.ready_reason.lower()


# ------------------ HTTP API ------------------


def test_http_crud_round_trip_for_docs_config() -> None:
    client = TestClient(app)
    create_payload = {
        "tool_type": "docs",
        "name": "api-docs",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "default_top_k": 3,
        "bm25_enabled": True,
        "fusion_strategy": "hybrid_rrf",
    }
    response = client.post("/api/v1/search-tools", json=create_payload)
    assert response.status_code == 201, response.text
    body = response.json()
    config_id = body["id"]
    assert body["tool_type"] == "docs"
    assert body["bm25_enabled"] is True
    assert body["fusion_strategy"] == "hybrid_rrf"

    listing = client.get("/api/v1/search-tools", params={"tool_type": "docs"})
    assert listing.status_code == 200
    assert any(entry["id"] == config_id for entry in listing.json())

    updated = client.patch(
        f"/api/v1/search-tools/{config_id}",
        json={"default_top_k": 10, "bm25_enabled": False, "fusion_strategy": "semantic_only"},
    )
    assert updated.status_code == 200
    assert updated.json()["default_top_k"] == 10
    assert updated.json()["bm25_enabled"] is False

    deleted = client.delete(f"/api/v1/search-tools/{config_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/search-tools/{config_id}")
    assert missing.status_code == 404


def test_http_rejects_invalid_docs_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/search-tools",
        json={
            "tool_type": "docs",
            "name": "oops",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "collection_target": "documents",
            "document_ids": [],
        },
    )
    assert response.status_code == 400


# ------------------ Run pipelines ------------------


def test_run_docs_bm25_only_returns_ranked_hits() -> None:
    _seed_document_chunks()
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import (
        SearchToolConfigCreateRequest,
        SearchToolRunRequest,
    )

    config = svc.create(
        SearchToolConfigCreateRequest(
            tool_type="docs",
            name="bm25-run",
            provider="openai",
            model="gpt-4o-mini",
            bm25_enabled=True,
            fusion_strategy="bm25_only",
            default_top_k=5,
        )
    )
    response = svc.run(config.id, SearchToolRunRequest(query="beta system"))
    assert response.tool_name == "supersearch.docs"
    assert response.status in {"success", "partial"}
    assert len(response.evidence) >= 1
    # Top hit must mention the keyword.
    assert any("beta" in ev.content.lower() for ev in response.evidence)


def test_run_unknown_config_raises_not_found() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import SearchToolRunRequest

    with pytest.raises(SearchToolConfigNotFoundError):
        svc.run("does-not-exist", SearchToolRunRequest(query="x"))


def test_run_graph_without_published_ontology_returns_partial_and_no_evidence() -> None:
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import (
        SearchToolConfigCreateRequest,
        SearchToolRunRequest,
    )

    config = svc.create(
        SearchToolConfigCreateRequest(
            tool_type="graph",
            name="graph-empty",
            provider="openai",
            model="gpt-4o-mini",
            ontology_scope="published",
        )
    )
    response = svc.run(config.id, SearchToolRunRequest(query="anything"))
    assert response.tool_name == "supersearch.graph"
    assert response.evidence == []
    assert response.status == "partial"


# ------------------ Tool registration ------------------


def test_supersearch_tools_registered_in_tool_registry() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    tool_names = {entry["tool_name"] for entry in response.json()}
    assert "supersearch.docs" in tool_names
    assert "supersearch.graph" in tool_names
