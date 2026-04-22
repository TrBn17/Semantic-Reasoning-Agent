from __future__ import annotations

from io import BytesIO
from urllib.parse import quote

from minio import Minio

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.ports.object_store import ObjectStorePort, StoredObject


class MinioBlobStore(ObjectStorePort):
    def __init__(self, settings: Settings, client: Minio | None = None) -> None:
        self._settings = settings
        self._bucket = settings.object_store_bucket
        self._client = client or Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def put_document_binary(
        self,
        document_id: str,
        filename: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> StoredObject:
        object_key = f"documents/{document_id}/source/{filename}"
        return self._put_bytes(
            object_key=object_key,
            content=content,
            content_type=content_type or "application/octet-stream",
        )

    def get_document_binary(
        self,
        document_id: str,
        object_key: str | None,
        fallback_content: bytes | None = None,
    ) -> bytes:
        del document_id
        if not object_key:
            return fallback_content or b""
        response = self._client.get_object(self._bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def put_artifact_binary(
        self,
        document_id: str,
        artifact_name: str,
        content: bytes,
        *,
        content_type: str,
        artifact_type: str,
    ) -> StoredObject:
        object_key = f"documents/{document_id}/artifacts/{artifact_type}/{artifact_name}"
        return self._put_bytes(
            object_key=object_key,
            content=content,
            content_type=content_type,
            metadata={"artifact_type": artifact_type},
        )

    def _put_bytes(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> StoredObject:
        self._client.put_object(
            self._bucket,
            object_key,
            data=BytesIO(content),
            length=len(content),
            content_type=content_type,
            metadata=metadata,
        )
        return StoredObject(
            object_key=object_key,
            bucket=self._bucket,
            uri=f"minio://{self._bucket}/{object_key}",
            public_url=self._public_url(object_key),
            content_type=content_type,
            size_bytes=len(content),
            metadata=metadata or {},
        )

    def _public_url(self, object_key: str) -> str:
        base = self._settings.minio_public_base_url.rstrip("/")
        return f"{base}/{self._bucket}/{quote(object_key)}"
