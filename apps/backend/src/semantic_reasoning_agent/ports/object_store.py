from __future__ import annotations

from typing import Protocol


class ObjectStorePort(Protocol):
    def put_document_binary(self, document_id: str, content: bytes) -> bytes:
        ...

    def get_document_binary(self, document_id: str, content: bytes) -> bytes:
        ...
