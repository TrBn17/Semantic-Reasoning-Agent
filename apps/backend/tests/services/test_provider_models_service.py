from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from semantic_reasoning_agent.services.provider_models_service import (
    CloudflareModelsClient,
    ProviderModel,
    ProviderModelsService,
)


def test_cloudflare_models_provider_uses_account_id_from_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    async def _fake_get_models(self: CloudflareModelsClient) -> list[ProviderModel]:
        captured["api_key"] = self.api_key
        captured["account_id"] = self.account_id
        return [ProviderModel(id="@cf/meta/llama-3.1-8b-instruct")]

    monkeypatch.setattr(CloudflareModelsClient, "get_models", _fake_get_models)

    settings = SimpleNamespace(
        openai_api_key=None,
        openai_base_url=None,
        openrouter_api_key=None,
        openrouter_base_url=None,
        cloudflare_api_key=None,
        cloudflare_account_id=None,
        anthropic_api_key=None,
        anthropic_base_url=None,
        google_api_key=None,
        ollama_base_url="http://localhost:11434",
    )
    service = ProviderModelsService(settings)

    models = asyncio.run(
        service.get_provider_models(
            "cloudflare",
            api_key="cf-token",
            base_url="https://api.cloudflare.com/client/v4/accounts/account-xyz/ai/v1",
        )
    )

    assert captured["api_key"] == "cf-token"
    assert captured["account_id"] == "account-xyz"
    assert models[0].id == "@cf/meta/llama-3.1-8b-instruct"


def test_cloudflare_models_provider_requires_account_id() -> None:
    settings = SimpleNamespace(
        openai_api_key=None,
        openai_base_url=None,
        openrouter_api_key=None,
        openrouter_base_url=None,
        cloudflare_api_key="cf-token",
        cloudflare_account_id=None,
        anthropic_api_key=None,
        anthropic_base_url=None,
        google_api_key=None,
        ollama_base_url="http://localhost:11434",
    )
    service = ProviderModelsService(settings)

    with pytest.raises(ValueError, match="Cloudflare account id not configured"):
        asyncio.run(service.get_provider_models("cloudflare"))


def test_cloudflare_models_client_filters_to_chat_models_and_uses_name_slug() -> None:
    chat_item = {
        "id": "41ca173f-72d5-4420-8915-49e835d2676e",
        "name": "@cf/meta/llama-3.1-8b-instruct",
        "task": {"name": "Text Generation"},
    }
    embedding_item = {
        "id": "eed32bc1-8775-4985-89ce-dd1405508ad8",
        "name": "@cf/baai/bge-m3",
        "task": {"name": "Text Embeddings"},
    }

    assert CloudflareModelsClient._is_chat_model(chat_item) is True
    assert CloudflareModelsClient._is_chat_model(embedding_item) is False
    assert chat_item["name"].startswith("@cf/")
