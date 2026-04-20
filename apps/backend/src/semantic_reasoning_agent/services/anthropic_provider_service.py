from __future__ import annotations

from semantic_reasoning_agent.core.config import Settings, get_settings

DEFAULT_ANTHROPIC_PROVIDER = "anthropic"
PRO_X_PROVIDER = "pro-x.io.vn"

ANTHROPIC_PROVIDER_OPTIONS: tuple[str, ...] = (
    DEFAULT_ANTHROPIC_PROVIDER,
    PRO_X_PROVIDER,
)

_ANTHROPIC_PROVIDER_BASE_URLS: dict[str, str | None] = {
    DEFAULT_ANTHROPIC_PROVIDER: None,
    PRO_X_PROVIDER: "http://pro-x.io.vn",
}


def normalize_anthropic_provider(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        return DEFAULT_ANTHROPIC_PROVIDER
    if normalized in ANTHROPIC_PROVIDER_OPTIONS:
        return normalized
    return DEFAULT_ANTHROPIC_PROVIDER


def provider_from_base_url(base_url: str | None) -> str:
    normalized = (base_url or "").strip().rstrip("/")
    if not normalized:
        return DEFAULT_ANTHROPIC_PROVIDER
    if normalized == "http://pro-x.io.vn":
        return PRO_X_PROVIDER
    return DEFAULT_ANTHROPIC_PROVIDER


def resolve_anthropic_base_url(
    *,
    provider_target: str | None = None,
    explicit_base_url: str | None = None,
) -> str | None:
    normalized_base_url = (explicit_base_url or "").strip().rstrip("/")
    if normalized_base_url:
        return normalized_base_url
    normalized_provider = normalize_anthropic_provider(provider_target)
    return _ANTHROPIC_PROVIDER_BASE_URLS.get(normalized_provider)


def settings_anthropic_provider(settings: Settings | None = None) -> str:
    cfg = settings or get_settings()
    return normalize_anthropic_provider(
        cfg.anthropic_provider_target or provider_from_base_url(cfg.anthropic_base_url)
    )
