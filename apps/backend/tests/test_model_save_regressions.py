from fastapi.testclient import TestClient

from semantic_reasoning_agent.main import app


client = TestClient(app)


def _provider_field_value(payload: dict, provider: str, key: str) -> dict:
    provider_payload = next(item for item in payload["providers"] if item["provider"] == provider)
    return next(item for item in provider_payload["values"] if item["key"] == key)


def test_settings_update_preserves_omitted_non_secret_provider_fields() -> None:
    workspace_id = "workspace-save-regression"
    first = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": workspace_id,
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {
                        "OPENAI_API_KEY": "demo-openai-key",
                        "OPENAI_BASE_URL": "https://example.local/v1",
                    },
                }
            ],
        },
    )
    assert first.status_code == 200

    second = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": workspace_id,
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {
                        "OPENAI_API_KEY": "demo-openai-key-updated",
                    },
                }
            ],
        },
    )
    assert second.status_code == 200

    latest = client.get("/api/v1/settings", params={"workspace_id": workspace_id})
    assert latest.status_code == 200
    field_value = _provider_field_value(latest.json(), "openai", "OPENAI_BASE_URL")
    assert field_value["configured"] is True
    assert field_value["source"] == "database"
    assert field_value["display_value"] == "https://example.local/v1"


def test_settings_update_preserves_existing_secret_when_client_sends_blank_secret() -> None:
    workspace_id = "workspace-secret-regression"
    first = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": workspace_id,
            "providers": [
                {
                    "provider": "openai",
                    "enabled": False,
                    "values": {
                        "OPENAI_API_KEY": "demo-openai-key",
                    },
                }
            ],
        },
    )
    assert first.status_code == 200

    second = client.put(
        "/api/v1/settings",
        json={
            "workspace_id": workspace_id,
            "providers": [
                {
                    "provider": "openai",
                    "enabled": True,
                    "values": {
                        "OPENAI_API_KEY": "",
                    },
                }
            ],
        },
    )
    assert second.status_code == 200

    latest = client.get("/api/v1/settings", params={"workspace_id": workspace_id})
    assert latest.status_code == 200
    provider_payload = next(item for item in latest.json()["providers"] if item["provider"] == "openai")
    assert provider_payload["enabled"] is True
    field_value = _provider_field_value(latest.json(), "openai", "OPENAI_API_KEY")
    assert field_value["configured"] is True
    assert field_value["source"] == "database"
    assert field_value["display_value"] != ""


def test_profile_patch_without_task_models_preserves_existing_assignments() -> None:
    create = client.post(
        "/api/v1/agents/profiles",
        json={
            "workspace_id": "workspace-demo",
            "name": "Regression Preserve Task Models",
            "task_models": [
                {
                    "task_type": "chat",
                    "provider": "echo",
                    "model": "local-echo",
                }
            ],
        },
    )
    assert create.status_code == 201
    created = create.json()
    assert len(created["task_models"]) == 1

    update = client.patch(
        f"/api/v1/agents/profiles/{created['id']}",
        json={
            "description": "updated-only-description",
        },
    )
    assert update.status_code == 200
    updated = update.json()
    assert len(updated["task_models"]) == 1
    assert updated["task_models"][0]["task_type"] == "chat"
    assert updated["task_models"][0]["provider"] == "echo"
    assert updated["task_models"][0]["model"] == "local-echo"
