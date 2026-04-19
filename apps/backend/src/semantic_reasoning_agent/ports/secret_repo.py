from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SecretDescriptor:
    configured: bool
    source: str
    masked_value: str = ""


class SecretRepository(Protocol):
    def set_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
        value: str,
    ) -> None:
        ...

    def get_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> str | None:
        ...

    def delete_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> None:
        ...

    def describe_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
    ) -> SecretDescriptor:
        ...
