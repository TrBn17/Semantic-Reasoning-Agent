"""Compatibility shim. Canonical implementation: ``semantic_reasoning_agent.application.chat_stream_service``."""

from semantic_reasoning_agent.application.chat_stream_service import (
    ChatStreamService,
    ProviderNotReadyError,
)

__all__ = ["ChatStreamService", "ProviderNotReadyError"]
