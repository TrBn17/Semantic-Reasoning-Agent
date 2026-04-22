from __future__ import annotations

from semantic_reasoning_agent.ports.object_store import ObjectStorePort, StoredObject


class DatabaseBlobStore(ObjectStorePort):
    def __init__(self, bucket: str = "database-blobs") -> None:
        self._bucket = bucket

    def put_document_binary(
        self,
        document_id: str,
        filename: str,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> StoredObject:
        object_key = f"documents/{document_id}/source/{filename}"
        resolved_content_type = content_type or "application/octet-stream"
        return StoredObject(
            object_key=object_key,
            bucket=self._bucket,
            uri=f"db://{object_key}",
            public_url=f"db://{object_key}",
            content_type=resolved_content_type,
            size_bytes=len(content),
        )

    def get_document_binary(
        self,
        document_id: str,
        object_key: str | None,
        fallback_content: bytes | None = None,
    ) -> bytes:
        del document_id, object_key
        return fallback_content or b""

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
        return StoredObject(
            object_key=object_key,
            bucket=self._bucket,
            uri=f"db://{object_key}",
            public_url=f"db://{object_key}",
            content_type=content_type,
            size_bytes=len(content),
            metadata={"artifact_type": artifact_type},
        )
