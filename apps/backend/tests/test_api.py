from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app
from semantic_reasoning_agent.services.provider_models_service import (
    AnthropicModelsClient,
    OpenAIModelsClient,
    OpenRouterModelsClient,
)


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
    response = client.get("/api/v1/settings/models")
    assert response.status_code == 200

    models = response.json()
    assert any(item["provider"] == "echo" and item["ready"] is True for item in models)


def test_public_settings_bootstrap_exposes_business_first_contract() -> None:
    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace"]["id"] == "workspace-demo"
    assert payload["workspace"]["name"] == "Demo Workspace"
    assert "model_catalog" in payload
    assert "task_defaults" in payload
    assert "models" not in payload
    assert any(item["use_case"] == "chat_default" for item in payload["task_defaults"])
    assert any(item["provider"] == "echo" for item in payload["model_catalog"])


def test_removed_compatibility_aliases_return_not_found() -> None:
    canonical = client.get("/api/v1/settings/models")
    alias_models = client.get("/api/v1/models")
    alias_catalog = client.get("/api/v1/agents/catalog")
    alias_settings_get = client.get("/api/v1/agents/settings")
    alias_settings_put = client.put(
        "/api/v1/agents/settings",
        json={"workspace_id": "workspace-demo", "providers": [], "task_assignments": []},
    )

    assert canonical.status_code == 200
    assert alias_models.status_code == 404
    assert alias_catalog.status_code == 404
    assert alias_settings_get.status_code == 404
    assert alias_settings_put.status_code == 404


def test_public_settings_update_round_trips_with_canonical_contract(monkeypatch) -> None:
    async def _raise_runtime_error(self):
        raise RuntimeError("upstream list-models unavailable")

    monkeypatch.setattr(OpenRouterModelsClient, "get_models", _raise_runtime_error)
    update_response = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": "workspace-settings",
            "providers": [
                {
                    "provider": "openrouter",
                    "enabled": True,
                    "values": {"OPENROUTER_API_KEY": "demo-openrouter-key"},
                }
            ],
            "task_defaults": [
                {
                    "use_case": "chat_default",
                    "provider": "openrouter",
                    "model": "nvidia/nemotron-3-super-120b-a12b:free",
                }
            ],
        },
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["workspace"]["id"] == "workspace-settings"
    assert payload["preferred_default_chat_model"]["provider"] == "openrouter"

    settings_response = client.get("/api/v1/settings", params={"workspace_id": "workspace-settings"})
    assert settings_response.status_code == 200
    assert settings_response.json()["workspace"]["id"] == "workspace-settings"
    chat_assignment = next(
        item for item in settings_response.json()["task_defaults"] if item["task_type"] == "chat"
    )
    assert chat_assignment["provider"] == "openrouter"
    assert chat_assignment["model"] == "nvidia/nemotron-3-super-120b-a12b:free"


def test_settings_can_persist_provider_and_task_assignments() -> None:
    update_response = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": "workspace-demo",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_defaults": [
                {
                    "use_case": "chat_default",
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
    assert "demo-openai-key" not in openai_provider["values"][0]["display_value"]

    chat_assignment = next(item for item in payload["task_defaults"] if item["task_type"] == "chat")
    assert chat_assignment["provider"] == "openai"
    assert chat_assignment["model"] == "gpt-5-mini"
    assert chat_assignment["ready"] is False
    assert "runtime" in chat_assignment["reason"].lower()


def test_model_catalog_uses_workspace_specific_provider_config() -> None:
    client.put(
        "/api/v1/settings",
        json={
            "workspace_id": "workspace-openai",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_defaults": [],
        },
    )

    response = client.get("/api/v1/settings", params={"workspace_id": "workspace-openai"})
    assert response.status_code == 200
    payload = response.json()
    openai = next(item for item in payload["providers"] if item["provider"] == "openai")
    assert openai["enabled"] is True
    assert openai["ready"] is False


def test_provider_models_endpoint_uses_workspace_specific_provider_config(monkeypatch) -> None:
    async def _raise_runtime_error(self):
        raise RuntimeError("upstream list-models unavailable")

    monkeypatch.setattr(OpenAIModelsClient, "get_models", _raise_runtime_error)

    client.put(
        "/api/v1/settings",
        json={
            "workspace_id": "workspace-openai-provider-endpoint",
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {"OPENAI_API_KEY": "demo-openai-key"},
                }
            ],
            "task_defaults": [],
        },
    )

    response = client.get(
        "/api/v1/providers/openai/models",
        params={"workspace_id": "workspace-openai-provider-endpoint"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai"
    assert any(item["id"] == "gpt-5-mini" for item in payload["models"])


def test_model_catalog_falls_back_to_maintained_anthropic_catalog(monkeypatch) -> None:
    async def _raise_runtime_error(self):
        raise RuntimeError("upstream list-models unavailable")

    monkeypatch.setattr(AnthropicModelsClient, "get_models", _raise_runtime_error)

    update_response = client.put(
        "/api/v1/settings",
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
            "task_defaults": [],
        },
    )
    assert update_response.status_code == 200

    response = client.get("/api/v1/settings/models", params={"workspace_id": "workspace-anthropic"})
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
    assert len(payload["conversation"]["messages"]) == 2


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
