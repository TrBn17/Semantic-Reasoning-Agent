from semantic_reasoning_agent.services.anthropic_provider_service import (
    DEFAULT_ANTHROPIC_PROVIDER,
    PRO_X_PROVIDER,
    provider_from_base_url,
    resolve_anthropic_base_url,
)


def test_resolve_anthropic_base_url_uses_provider_target_mapping() -> None:
    assert resolve_anthropic_base_url(provider_target=DEFAULT_ANTHROPIC_PROVIDER) is None
    assert resolve_anthropic_base_url(provider_target=PRO_X_PROVIDER) == "http://pro-x.io.vn"


def test_resolve_anthropic_base_url_prefers_explicit_legacy_value() -> None:
    assert (
        resolve_anthropic_base_url(
            provider_target=DEFAULT_ANTHROPIC_PROVIDER,
            explicit_base_url="http://legacy-gateway.local/",
        )
        == "http://legacy-gateway.local"
    )


def test_provider_from_base_url_detects_pro_x_gateway() -> None:
    assert provider_from_base_url("http://pro-x.io.vn/") == PRO_X_PROVIDER
