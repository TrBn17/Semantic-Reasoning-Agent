from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from semantic_reasoning_agent.db.database import DatabaseManager
from semantic_reasoning_agent.db.models import ProviderSecretORM


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SecretDescriptor:
    configured: bool
    source: str
    masked_value: str = ""


class SecretRepository:
    def set_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
        value: str,
    ) -> None:
        raise NotImplementedError

    def get_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> str | None:
        raise NotImplementedError

    def delete_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> None:
        raise NotImplementedError

    def describe_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
    ) -> SecretDescriptor:
        raise NotImplementedError


class DatabaseSecretRepository(SecretRepository):
    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def set_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
        value: str,
    ) -> None:
        secret_id = f"{workspace_id}:{provider}:{field_key}"
        with self._database_manager.session() as session:
            existing = session.get(ProviderSecretORM, secret_id)
            if existing is None:
                session.add(
                    ProviderSecretORM(
                        id=secret_id,
                        workspace_id=workspace_id,
                        provider=provider,
                        field_key=field_key,
                        secret_value=value,
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    )
                )
            else:
                existing.secret_value = value
                existing.updated_at = utc_now()

    def get_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> str | None:
        with self._database_manager.session() as session:
            record = session.scalar(
                select(ProviderSecretORM).where(
                    ProviderSecretORM.workspace_id == workspace_id,
                    ProviderSecretORM.provider == provider,
                    ProviderSecretORM.field_key == field_key,
                )
            )
            return None if record is None else record.secret_value

    def delete_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> None:
        with self._database_manager.session() as session:
            record = session.scalar(
                select(ProviderSecretORM).where(
                    ProviderSecretORM.workspace_id == workspace_id,
                    ProviderSecretORM.provider == provider,
                    ProviderSecretORM.field_key == field_key,
                )
            )
            if record is not None:
                session.delete(record)

    def describe_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
    ) -> SecretDescriptor:
        value = self.get_provider_secret(workspace_id, provider, field_key)
        if not value:
            return SecretDescriptor(configured=False, source="missing", masked_value="")
        return SecretDescriptor(
            configured=True,
            source="database",
            masked_value=self._mask_value(value),
        )

    @staticmethod
    def _mask_value(value: str) -> str:
        if len(value) <= 4:
            return "*" * len(value)
        return f"{value[:2]}{'*' * max(4, len(value) - 4)}{value[-2:]}"


class SecretService:
    def __init__(self, repository: SecretRepository) -> None:
        self._repository = repository

    def set_provider_secret(self, workspace_id: str, provider: str, field_key: str, value: str) -> None:
        self._repository.set_provider_secret(workspace_id, provider, field_key, value)

    def get_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> str | None:
        return self._repository.get_provider_secret(workspace_id, provider, field_key)

    def delete_provider_secret(self, workspace_id: str, provider: str, field_key: str) -> None:
        self._repository.delete_provider_secret(workspace_id, provider, field_key)

    def describe_provider_secret(
        self,
        workspace_id: str,
        provider: str,
        field_key: str,
    ) -> SecretDescriptor:
        return self._repository.describe_provider_secret(workspace_id, provider, field_key)
