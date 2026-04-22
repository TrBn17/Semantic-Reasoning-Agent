from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    bucket: str
    uri: str
    public_url: str
    content_type: str
    size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ObjectStorePort(Protocol):
    def put_document_binary(
        self,
        document_id: str,
        filename: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> StoredObject:
        ...

    def get_document_binary(
        self,
        document_id: str,
        object_key: str | None,
        fallback_content: bytes | None = None,
    ) -> bytes:
        ...

    def put_artifact_binary(
        self,
        document_id: str,
        artifact_name: str,
        content: bytes,
        *,
        content_type: str,
        artifact_type: str,
    ) -> StoredObject:
        ...
