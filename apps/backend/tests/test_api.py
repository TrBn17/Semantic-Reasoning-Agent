from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_me_contract() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200

    payload = response.json()
    assert payload["id"] == "user-demo"
    assert payload["active_workspace"]["id"] == "workspace-demo"


def test_model_catalog_includes_local_echo() -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 200

    models = response.json()
    assert any(item["provider"] == "echo" and item["ready"] is True for item in models)


def test_create_conversation_and_send_echo_message() -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Phase 1 prep", "provider": "echo", "model": "local-echo"},
    )
    assert create_response.status_code == 201

    conversation = create_response.json()
    send_response = client.post(
        "/api/v1/chat/messages",
        json={
            "conversation_id": conversation["id"],
            "content": "hello",
            "provider": "echo",
            "model": "local-echo",
        },
    )
    assert send_response.status_code == 201

    payload = send_response.json()
    assert payload["reply"]["role"] == "assistant"
    assert payload["reply"]["content"] == "echo: hello"
    assert payload["citations"] == []
    assert len(payload["conversation"]["messages"]) == 2


def test_unready_provider_is_rejected() -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Anthropic later", "provider": "anthropic", "model": "claude-sonnet-4-5"},
    )
    conversation = create_response.json()

    send_response = client.post(
        "/api/v1/chat/messages",
        json={
            "conversation_id": conversation["id"],
            "content": "hello",
            "provider": "anthropic",
            "model": "claude-sonnet-4-5",
        },
    )

    assert send_response.status_code == 400
    assert "not ready yet" in send_response.json()["detail"]
