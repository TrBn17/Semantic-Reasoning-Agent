from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app


client = TestClient(app)


def test_knowledge_pack_crud_and_document_membership() -> None:
    create_response = client.post(
        "/api/v1/knowledge-packs",
        json={
            "workspace_id": "workspace-demo",
            "name": "Policies",
        },
    )
    assert create_response.status_code == 201
    pack = create_response.json()
    pack_id = pack["id"]

    listed = client.get("/api/v1/knowledge-packs", params={"workspace_id": "workspace-demo"})
    assert listed.status_code == 200
    assert any(item["id"] == pack_id for item in listed.json())

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("policy.csv", b"id,title\n1,Security\n", "text/csv")},
        data={
            "workspace_id": "workspace-demo",
            "ingestion_mode": "retrieval",
            "knowledge_pack_id": pack_id,
        },
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    members = client.get(f"/api/v1/knowledge-packs/{pack_id}/documents")
    assert members.status_code == 200
    assert any(item["document_id"] == document_id for item in members.json())

    remove = client.delete(f"/api/v1/knowledge-packs/{pack_id}/documents/{document_id}")
    assert remove.status_code == 200

    delete_response = client.delete(f"/api/v1/knowledge-packs/{pack_id}")
    assert delete_response.status_code == 204
