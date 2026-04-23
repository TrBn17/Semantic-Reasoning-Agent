"""Integration tests for the supersearch.docs / supersearch.graph pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from semantic_reasoning_agent.core.container import get_app_container
from semantic_reasoning_agent.main import app
from semantic_reasoning_agent.persistence.models import (
    DocumentChunkORM,
    DocumentORM,
    OntologyEntityFactORM,
    OntologyEntityORM,
    OntologyEntityTypeDefinitionORM,
    OntologyRelationORM,
    OntologyRelationTypeDefinitionORM,
    OntologyVersionORM,
)
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
    retrieval_service = container.retrieval_service
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
            embedding = retrieval_service.embed_text(text, workspace_id=WORKSPACE_ID)
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
                    embedding=embedding,
                    embedding_provider="token",
                    embedding_model="token-fallback",
                    created_at=now,
                )
            )
            chunk_ids.append(cid)
    return chunk_ids


def _seed_ontology_with_facts() -> None:
    container = get_app_container()
    now = datetime.now(timezone.utc)
    with container.database_manager.session() as session:
        version = OntologyVersionORM(
            id="ver-1",
            workspace_id=WORKSPACE_ID,
            version_number=1,
            source_build_id="build-1",
            ontology_title="Test Graph",
            ontology_summary="seed",
            created_at=now,
        )
        entity = OntologyEntityORM(
            id="entity-1",
            version_id=version.id,
            workspace_id=WORKSPACE_ID,
            resolution_key="sensor-a",
            name="Sensor A",
            entity_type="sensor",
            aliases=[],
            query_rules=[],
            source_build_id="build-1",
            source_document_id="doc-1",
            created_at=now,
        )
        relation = OntologyRelationORM(
            id="relation-1",
            version_id=version.id,
            workspace_id=WORKSPACE_ID,
            source_entity_id=entity.id,
            target_entity_id=entity.id,
            relation_type="reports",
            confidence=1.0,
            source_build_id="build-1",
            source_document_id="doc-1",
            evidence_text="Sensor reports values.",
            provenance={},
            query_rules=[],
            created_at=now,
        )
        entity_type = OntologyEntityTypeDefinitionORM(
            id="entity-type-1",
            version_id=version.id,
            workspace_id=WORKSPACE_ID,
            name="sensor",
            description="Sensor entity",
            attributes=[],
            query_rules=[
                {
                    "rule_id": "sensor-threshold-rule",
                    "scope": "entity_type",
                    "query_route": "sql_facts",
                    "trigger_keywords": ["threshold", "sensor"],
                }
            ],
            examples=["Sensor A"],
            created_at=now,
        )
        relation_type = OntologyRelationTypeDefinitionORM(
            id="relation-type-1",
            version_id=version.id,
            workspace_id=WORKSPACE_ID,
            name="reports",
            description="report relation",
            attributes=[],
            query_rules=[],
            allowed_source_targets=[],
            created_at=now,
        )
        fact = OntologyEntityFactORM(
            id="fact-1",
            workspace_id=WORKSPACE_ID,
            version_id=version.id,
            entity_id=entity.id,
            metric_key="maintenance_threshold",
            value_num=80.0,
            value_text=None,
            value_bool=None,
            unit="percent",
            observed_at=now,
            source_document_id="doc-1",
            source_chunk_id="chunk-1",
            metadata_json={},
            created_at=now,
        )
        session.add(version)
        session.add(entity)
        session.add(relation)
        session.add(entity_type)
        session.add(relation_type)
        session.add(fact)


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


def test_service_auto_provisions_workspace_defaults() -> None:
    configs = _service().list()
    system_keys = {config.system_key for config in configs if config.is_system}
    assert "workspace_default_rag" in system_keys
    assert "workspace_default_ontology_search" in system_keys


def test_service_duplicate_creates_custom_copy_for_system_tool() -> None:
    svc = _service()
    system_tool = next(config for config in svc.list() if config.system_key == "workspace_default_rag")
    duplicated = svc.duplicate(system_tool.id)
    assert duplicated.is_system is False
    assert duplicated.name.startswith(system_tool.name)
    assert duplicated.embedding_provider == system_tool.embedding_provider


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


def test_http_system_search_tool_cannot_be_deleted_but_can_be_duplicated() -> None:
    client = TestClient(app)
    configs = client.get("/api/v1/search-tools").json()
    system_tool = next(item for item in configs if item["system_key"] == "workspace_default_rag")

    delete_response = client.delete(f"/api/v1/search-tools/{system_tool['id']}")
    assert delete_response.status_code == 400

    duplicate_response = client.post(f"/api/v1/search-tools/{system_tool['id']}/duplicate")
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["is_system"] is False


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


def test_run_graph_uses_sql_facts_route_when_rule_matches() -> None:
    _seed_ontology_with_facts()
    svc = _service()
    from semantic_reasoning_agent.schemas.search_tools import (
        SearchToolConfigCreateRequest,
        SearchToolRunRequest,
    )

    config = svc.create(
        SearchToolConfigCreateRequest(
            tool_type="graph",
            name="graph-facts",
            provider="openai",
            model="gpt-4o-mini",
            ontology_scope="published",
        )
    )
    response = svc.run(config.id, SearchToolRunRequest(query="sensor threshold"))

    assert response.status in {"success", "partial"}
    assert len(response.evidence) >= 1
    assert any(ev.citation_anchor.locator.startswith("ontology-entity-fact:") for ev in response.evidence)


# ------------------ Tool registration ------------------


def test_supersearch_tools_registered_in_tool_registry() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    tool_names = {entry["tool_name"] for entry in response.json()}
    assert "supersearch.docs" in tool_names
    assert "supersearch.graph" in tool_names
