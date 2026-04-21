from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app
from semantic_reasoning_agent.services.provider_models_service import AnthropicModelsClient


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


def test_agent_settings_can_persist_provider_and_task_assignments() -> None:
    update_response = client.put(
        "/api/v1/agents/settings",
        json={
            "workspace_id": "workspace-demo",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_assignments": [
                {
                    "task_type": "chat",
                    "provider": "openai",
                    "model": "gpt-5-mini",
                }
            ],
        },
    )
    assert update_response.status_code == 200
    payload = update_response.json()

    openai_provider = next(item for item in payload["providers"] if item["provider"] == "openai")
    assert openai_provider["values"][0]["configured"] is True
    assert openai_provider["values"][0]["source"] == "database"
    assert "demo-openai-key" not in openai_provider["values"][0]["masked_value"]

    chat_assignment = next(item for item in payload["task_assignments"] if item["task_type"] == "chat")
    assert chat_assignment["provider"] == "openai"
    assert chat_assignment["model"] == "gpt-5-mini"
    assert chat_assignment["ready"] is False
    assert "adapter runtime" in chat_assignment["reason"]


def test_model_catalog_uses_workspace_specific_provider_config() -> None:
    client.put(
        "/api/v1/agents/settings",
        json={
            "workspace_id": "workspace-openai",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_assignments": [],
        },
    )

    response = client.get("/api/v1/models", params={"workspace_id": "workspace-openai"})
    assert response.status_code == 200
    models = response.json()
    openai = next(item for item in models if item["provider"] == "openai")
    assert openai["missing_env_fields"] == []
    assert openai["ready"] is False


def test_model_catalog_falls_back_to_maintained_anthropic_catalog(monkeypatch) -> None:
    async def _raise_runtime_error(self):
        raise RuntimeError("upstream list-models unavailable")

    monkeypatch.setattr(AnthropicModelsClient, "get_models", _raise_runtime_error)

    update_response = client.put(
        "/api/v1/agents/settings",
        json={
            "workspace_id": "workspace-anthropic",
            "providers": [
                {
                    "provider": "anthropic",
                    "enabled": True,
                    "values": {
                        "ANTHROPIC_API_KEY": "demo-ant-key",
                        "ANTHROPIC_BASE_URL": "https://example.invalid",
                    },
                }
            ],
            "task_assignments": [],
        },
    )
    assert update_response.status_code == 200

    response = client.get("/api/v1/models", params={"workspace_id": "workspace-anthropic"})
    assert response.status_code == 200
    models = response.json()

    anthropic_models = [item for item in models if item["provider"] == "anthropic"]
    assert anthropic_models
    assert any(item["model"] == "claude-sonnet-4-5" for item in anthropic_models)
    assert any(item["model"] == "claude-opus-4-0" and item["label"] == "Claude Opus 4.0" for item in anthropic_models)
    assert any(item["model"] == "claude-sonnet-4-5" and item["label"] == "Claude Sonnet 4.5" for item in anthropic_models)


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
    assert payload["tool_calls"] == []
    assert payload["conversation_id"] == conversation["id"]


def test_chat_stream_endpoint_emits_structured_events() -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Streaming chat", "provider": "echo", "model": "local-echo"},
    )
    conversation = create_response.json()

    with client.stream(
        "POST",
        "/api/v1/chat/messages/stream",
        json={
            "conversation_id": conversation["id"],
            "content": "hello stream",
            "provider": "echo",
            "model": "local-echo",
        },
    ) as response:
        assert response.status_code == 200
        payload = "".join(response.iter_text())

    assert "event: message_start" in payload
    assert "event: content_delta" in payload
    assert "event: message_complete" in payload
    assert "echo: hello stream" in payload


def test_default_agent_profile_drives_new_conversation_model() -> None:
    profile_response = client.post(
        "/api/v1/agents/profiles",
        json={
            "workspace_id": "workspace-demo",
            "name": "General Analyst",
            "system_prompt": "You are a precise analyst.",
            "is_default": True,
            "task_models": [
                {
                    "task_type": "chat",
                    "provider": "echo",
                    "model": "local-echo",
                }
            ],
            "tool_assignments": [{"tool_name": "retrieval.internal", "enabled": False}],
        },
    )
    assert profile_response.status_code == 201
    profile = profile_response.json()

    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Profile chat", "workspace_id": "workspace-demo"},
    )
    assert create_response.status_code == 201
    conversation = create_response.json()
    assert conversation["agent_profile_id"] == profile["id"]
    assert conversation["uses_model_override"] is False
    assert conversation["provider"] == "echo"
    assert conversation["effective_tool_names"] == ["ontology.lookup", "graph.search", "graph.ingest"]


def test_conversation_model_override_persists_per_session() -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Override chat", "workspace_id": "workspace-demo"},
    )
    conversation = create_response.json()

    update_response = client.patch(
        f"/api/v1/conversations/{conversation['id']}/model-selection",
        json={"provider": "echo", "model": "local-echo", "workspace_id": "workspace-demo"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["uses_model_override"] is True
    assert updated["provider"] == "echo"
    assert updated["model"] == "local-echo"


def test_conversation_model_override_rejects_unready_model() -> None:
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Bad override chat", "workspace_id": "workspace-demo"},
    )
    conversation = create_response.json()

    update_response = client.patch(
        f"/api/v1/conversations/{conversation['id']}/model-selection",
        json={"provider": "openai", "model": "gpt-5-mini", "workspace_id": "workspace-demo"},
    )
    assert update_response.status_code == 400
    assert "is not ready" in update_response.json()["detail"]


def test_profile_can_block_chat_model_override() -> None:
    profile_response = client.post(
        "/api/v1/agents/profiles",
        json={
            "workspace_id": "workspace-demo",
            "name": "Locked agent",
            "allow_chat_model_override": False,
            "task_models": [
                {
                    "task_type": "chat",
                    "provider": "echo",
                    "model": "local-echo",
                }
            ],
        },
    )
    profile = profile_response.json()

    create_response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Locked conversation",
            "workspace_id": "workspace-demo",
            "agent_profile_id": profile["id"],
        },
    )
    conversation = create_response.json()

    update_response = client.patch(
        f"/api/v1/conversations/{conversation['id']}/model-selection",
        json={"provider": "echo", "model": "local-echo", "workspace_id": "workspace-demo"},
    )
    assert update_response.status_code == 400
    assert "does not allow chat model override" in update_response.json()["detail"]


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


def test_conversation_creation_falls_back_to_ready_model_when_assignment_is_blocked() -> None:
    update_response = client.put(
        "/api/v1/agents/settings",
        json={
            "workspace_id": "workspace-demo",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_assignments": [
                {
                    "task_type": "chat",
                    "provider": "openai",
                    "model": "gpt-5-mini",
                }
            ],
        },
    )
    assert update_response.status_code == 200

    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Fallback chat", "workspace_id": "workspace-demo"},
    )
    assert create_response.status_code == 201
    conversation = create_response.json()

    assert conversation["provider"] == "echo"
    assert conversation["model"] == "local-echo"
    assert conversation["uses_model_override"] is False
