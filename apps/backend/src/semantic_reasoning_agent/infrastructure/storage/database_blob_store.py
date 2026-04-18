from __future__ import annotations

from semantic_reasoning_agent.ports.object_store import ObjectStorePort


class DatabaseBlobStore(ObjectStorePort):
    def put_document_binary(self, document_id: str, content: bytes) -> bytes:
        _ = document_id
        return content

    def get_document_binary(self, document_id: str, content: bytes) -> bytes:
        _ = document_id
        return content
