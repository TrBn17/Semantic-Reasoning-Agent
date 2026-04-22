from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.infrastructure.storage.database_blob_store import DatabaseBlobStore
from semantic_reasoning_agent.infrastructure.storage.minio_blob_store import MinioBlobStore
from semantic_reasoning_agent.ports.object_store import ObjectStorePort


def build_object_store(settings: Settings) -> ObjectStorePort:
    if settings.object_store_backend.lower() == "minio":
        return MinioBlobStore(settings)
    return DatabaseBlobStore()


__all__ = ["DatabaseBlobStore", "MinioBlobStore", "build_object_store"]
