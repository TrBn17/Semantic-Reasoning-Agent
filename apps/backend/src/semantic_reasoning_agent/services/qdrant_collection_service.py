from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import httpx

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.documents.models import IndexedChunk

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9_-]+")


class QdrantCollectionServiceError(RuntimeError):
    """Raised when a Qdrant operation fails."""


@dataclass(frozen=True)
class QdrantDocumentSummary:
    document_id: str
    document_title: str
    chunk_count: int


@dataclass(frozen=True)
class QdrantChunkRecord:
    chunk_id: str
    workspace_id: str
    document_id: str
    document_title: str
    document_type: str
    text: str
    source_url: str
    page_number: int | None
    heading_path: str | None
    sheet_name: str | None
    row_start: int | None
    row_end: int | None
    score: float | None = None


class QdrantCollectionService:
    """Thin Qdrant REST wrapper for workspace knowledge-pack collections."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base_url = settings.qdrant_url.rstrip("/")
        self._timeout = 20.0
        self._memory_mode = settings.app_env.lower() == "test"
        self._memory_collections: dict[str, dict[str, dict[str, Any]]] = {}

    def collection_name(self, workspace_id: str, knowledge_pack_id: str) -> str:
        safe_workspace = _SAFE_NAME.sub("_", workspace_id)
        safe_pack = _SAFE_NAME.sub("_", knowledge_pack_id)
        return f"kp__{safe_workspace}__{safe_pack}"

    def parse_pack_id(self, workspace_id: str, collection_name: str) -> str | None:
        prefix = f"kp__{_SAFE_NAME.sub('_', workspace_id)}__"
        if not collection_name.startswith(prefix):
            return None
        return collection_name.removeprefix(prefix)

    def ensure_collection(
        self,
        workspace_id: str,
        knowledge_pack_id: str,
        *,
        vector_size: int = 1024,
    ) -> str:
        name = self.collection_name(workspace_id, knowledge_pack_id)
        if self.collection_exists(name):
            return name
        self._request(
            "PUT",
            f"/collections/{name}",
            json_body={
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine",
                }
            },
        )
        return name

    def collection_exists(self, collection_name: str) -> bool:
        try:
            self._request("GET", f"/collections/{collection_name}")
            return True
        except QdrantCollectionServiceError:
            return False

    def list_workspace_pack_ids(self, workspace_id: str) -> list[str]:
        payload = self._request("GET", "/collections")
        collections = (payload.get("result") or {}).get("collections") or []
        pack_ids: list[str] = []
        for item in collections:
            name = str(item.get("name") or "")
            pack_id = self.parse_pack_id(workspace_id, name)
            if pack_id:
                pack_ids.append(pack_id)
        return sorted(set(pack_ids))

    def delete_collection(self, workspace_id: str, knowledge_pack_id: str) -> None:
        collection_name = self.collection_name(workspace_id, knowledge_pack_id)
        self._request("DELETE", f"/collections/{collection_name}")

    def upsert_chunks(
        self,
        workspace_id: str,
        knowledge_pack_id: str,
        chunks: list[IndexedChunk],
    ) -> None:
        if not chunks:
            return
        dense_chunk = next((chunk for chunk in chunks if isinstance(chunk.embedding, list)), None)
        if dense_chunk is None:
            raise QdrantCollectionServiceError(
                "Qdrant upsert requires dense vector embeddings, but only sparse payloads were provided."
            )
        vector_size = len(dense_chunk.embedding)
        collection_name = self.ensure_collection(
            workspace_id,
            knowledge_pack_id,
            vector_size=vector_size,
        )
        points: list[dict[str, Any]] = []
        for chunk in chunks:
            if not isinstance(chunk.embedding, list):
                continue
            points.append(
                {
                    "id": chunk.chunk_id,
                    "vector": chunk.embedding,
                    "payload": {
                        "workspace_id": chunk.workspace_id,
                        "knowledge_pack_id": knowledge_pack_id,
                        "document_id": chunk.document_id,
                        "document_title": chunk.document_title,
                        "document_type": chunk.document_type,
                        "text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "source_url": chunk.source_url,
                        "parser_version": chunk.parser_version,
                        "embedding_provider": chunk.embedding_provider,
                        "embedding_model": chunk.embedding_model,
                        "page_number": chunk.page_number,
                        "heading_path": chunk.heading_path,
                        "sheet_name": chunk.sheet_name,
                        "row_start": chunk.row_start,
                        "row_end": chunk.row_end,
                    },
                }
            )
        if not points:
            raise QdrantCollectionServiceError("No dense vectors available for Qdrant upsert.")
        self._request(
            "PUT",
            f"/collections/{collection_name}/points",
            params={"wait": "true"},
            json_body={"points": points},
        )

    def delete_document(self, workspace_id: str, knowledge_pack_id: str, document_id: str) -> None:
        collection_name = self.collection_name(workspace_id, knowledge_pack_id)
        if not self.collection_exists(collection_name):
            return
        self._request(
            "POST",
            f"/collections/{collection_name}/points/delete",
            params={"wait": "true"},
            json_body={
                "filter": {
                    "must": [
                        {"key": "workspace_id", "match": {"value": workspace_id}},
                        {"key": "document_id", "match": {"value": document_id}},
                    ]
                }
            },
        )

    def list_documents(
        self, workspace_id: str, knowledge_pack_id: str
    ) -> list[QdrantDocumentSummary]:
        chunks = self.list_chunks(
            workspace_id=workspace_id,
            knowledge_pack_ids=[knowledge_pack_id],
            limit=10_000,
        )
        grouped: dict[str, QdrantDocumentSummary] = {}
        for chunk in chunks:
            existing = grouped.get(chunk.document_id)
            if existing is None:
                grouped[chunk.document_id] = QdrantDocumentSummary(
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    chunk_count=1,
                )
                continue
            grouped[chunk.document_id] = QdrantDocumentSummary(
                document_id=existing.document_id,
                document_title=existing.document_title,
                chunk_count=existing.chunk_count + 1,
            )
        return sorted(grouped.values(), key=lambda item: item.document_title.lower())

    def list_chunks(
        self,
        *,
        workspace_id: str,
        knowledge_pack_ids: list[str] | None = None,
        document_ids: list[str] | None = None,
        limit: int = 5_000,
    ) -> list[QdrantChunkRecord]:
        collection_ids = knowledge_pack_ids or self.list_workspace_pack_ids(workspace_id)
        chunks: list[QdrantChunkRecord] = []
        for pack_id in collection_ids:
            collection_name = self.collection_name(workspace_id, pack_id)
            if not self.collection_exists(collection_name):
                continue
            points = self._scroll_points(
                collection_name=collection_name,
                workspace_id=workspace_id,
                document_ids=document_ids,
                with_vector=False,
                limit=limit,
            )
            for point in points:
                payload = point.get("payload") or {}
                chunks.append(
                    QdrantChunkRecord(
                        chunk_id=str(point.get("id") or ""),
                        workspace_id=str(payload.get("workspace_id") or workspace_id),
                        document_id=str(payload.get("document_id") or ""),
                        document_title=str(payload.get("document_title") or ""),
                        document_type=str(payload.get("document_type") or ""),
                        text=str(payload.get("text") or ""),
                        source_url=str(payload.get("source_url") or ""),
                        page_number=_as_int(payload.get("page_number")),
                        heading_path=_as_optional_str(payload.get("heading_path")),
                        sheet_name=_as_optional_str(payload.get("sheet_name")),
                        row_start=_as_int(payload.get("row_start")),
                        row_end=_as_int(payload.get("row_end")),
                    )
                )
        return chunks

    def collect_document_points_across_workspace(
        self,
        *,
        workspace_id: str,
        document_id: str,
        exclude_pack_id: str | None = None,
    ) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        for pack_id in self.list_workspace_pack_ids(workspace_id):
            if exclude_pack_id and pack_id == exclude_pack_id:
                continue
            collection_name = self.collection_name(workspace_id, pack_id)
            if not self.collection_exists(collection_name):
                continue
            points.extend(
                self._scroll_points(
                    collection_name=collection_name,
                    workspace_id=workspace_id,
                    document_ids=[document_id],
                    with_vector=True,
                    limit=10_000,
                )
            )
        return points

    def add_points_to_collection(
        self,
        *,
        workspace_id: str,
        knowledge_pack_id: str,
        points: list[dict[str, Any]],
    ) -> None:
        if not points:
            return
        first_vector = next(
            (point.get("vector") for point in points if isinstance(point.get("vector"), list)), None
        )
        if not isinstance(first_vector, list):
            raise QdrantCollectionServiceError("Cannot copy document without vector payload.")
        collection_name = self.ensure_collection(
            workspace_id,
            knowledge_pack_id,
            vector_size=len(first_vector),
        )
        self._request(
            "PUT",
            f"/collections/{collection_name}/points",
            params={"wait": "true"},
            json_body={"points": points},
        )

    def search(
        self,
        *,
        workspace_id: str,
        query_vector: list[float],
        top_k: int,
        knowledge_pack_ids: list[str] | None = None,
        document_ids: list[str] | None = None,
    ) -> list[QdrantChunkRecord]:
        if not query_vector:
            return []
        collection_ids = knowledge_pack_ids or self.list_workspace_pack_ids(workspace_id)
        hits: list[QdrantChunkRecord] = []
        for pack_id in collection_ids:
            collection_name = self.collection_name(workspace_id, pack_id)
            if not self.collection_exists(collection_name):
                continue
            payload = self._request(
                "POST",
                f"/collections/{collection_name}/points/search",
                json_body={
                    "vector": query_vector,
                    "limit": max(top_k, 1),
                    "with_payload": True,
                    "with_vector": False,
                    "filter": self._build_filter(
                        workspace_id=workspace_id, document_ids=document_ids
                    ),
                },
            )
            for point in payload.get("result") or []:
                point_payload = point.get("payload") or {}
                hits.append(
                    QdrantChunkRecord(
                        chunk_id=str(point.get("id") or ""),
                        workspace_id=str(point_payload.get("workspace_id") or workspace_id),
                        document_id=str(point_payload.get("document_id") or ""),
                        document_title=str(point_payload.get("document_title") or ""),
                        document_type=str(point_payload.get("document_type") or ""),
                        text=str(point_payload.get("text") or ""),
                        source_url=str(point_payload.get("source_url") or ""),
                        page_number=_as_int(point_payload.get("page_number")),
                        heading_path=_as_optional_str(point_payload.get("heading_path")),
                        sheet_name=_as_optional_str(point_payload.get("sheet_name")),
                        row_start=_as_int(point_payload.get("row_start")),
                        row_end=_as_int(point_payload.get("row_end")),
                        score=float(point.get("score") or 0.0),
                    )
                )
        hits.sort(key=lambda item: item.score or 0.0, reverse=True)
        return hits[:top_k]

    def _scroll_points(
        self,
        *,
        collection_name: str,
        workspace_id: str,
        document_ids: list[str] | None,
        with_vector: bool,
        limit: int,
    ) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        next_offset: Any = None
        while True:
            body: dict[str, Any] = {
                "limit": min(512, max(limit, 1)),
                "with_payload": True,
                "with_vector": with_vector,
                "filter": self._build_filter(workspace_id=workspace_id, document_ids=document_ids),
            }
            if next_offset is not None:
                body["offset"] = next_offset
            payload = self._request(
                "POST",
                f"/collections/{collection_name}/points/scroll",
                json_body=body,
            )
            result = payload.get("result") or {}
            batch = result.get("points") or []
            points.extend(batch)
            if len(points) >= limit:
                return points[:limit]
            next_offset = result.get("next_page_offset")
            if next_offset is None:
                return points

    @staticmethod
    def _build_filter(*, workspace_id: str, document_ids: list[str] | None) -> dict[str, Any]:
        must: list[dict[str, Any]] = [{"key": "workspace_id", "match": {"value": workspace_id}}]
        if document_ids:
            must.append({"key": "document_id", "match": {"any": sorted(set(document_ids))}})
        return {"must": must}

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if self._memory_mode:
            return self._request_memory(method, path, json_body=json_body)
        try:
            response = httpx.request(
                method=method,
                url=f"{self._base_url}{path}",
                json=json_body,
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict):
                return payload
            raise QdrantCollectionServiceError("Qdrant returned an unexpected response payload.")
        except Exception as exc:  # pragma: no cover - network/infra error
            raise QdrantCollectionServiceError(
                f"Qdrant request failed: {method} {path}: {exc}"
            ) from exc

    def _request_memory(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        segments = [segment for segment in path.strip("/").split("/") if segment]
        if segments == ["collections"] and method == "GET":
            return {
                "result": {
                    "collections": [
                        {"name": name} for name in sorted(self._memory_collections.keys())
                    ]
                }
            }
        if len(segments) >= 2 and segments[0] == "collections":
            collection_name = segments[1]
            if len(segments) == 2:
                if method == "GET":
                    if collection_name not in self._memory_collections:
                        raise QdrantCollectionServiceError(
                            f"Collection '{collection_name}' was not found."
                        )
                    return {"result": {"status": "green"}}
                if method == "PUT":
                    self._memory_collections.setdefault(collection_name, {})
                    return {"result": True}
                if method == "DELETE":
                    self._memory_collections.pop(collection_name, None)
                    return {"result": True}
            if len(segments) == 3 and segments[2] == "points" and method == "PUT":
                collection = self._memory_collections.setdefault(collection_name, {})
                points = (json_body or {}).get("points") or []
                for point in points:
                    point_id = str(point.get("id"))
                    collection[point_id] = point
                return {"result": {"status": "acknowledged"}}
            if len(segments) == 4 and segments[2] == "points":
                operation = segments[3]
                if operation == "delete" and method == "POST":
                    collection = self._memory_collections.setdefault(collection_name, {})
                    must = ((json_body or {}).get("filter") or {}).get("must") or []
                    doc_id = _extract_filter_value(must, "document_id")
                    workspace_id = _extract_filter_value(must, "workspace_id")
                    for point_id, point in list(collection.items()):
                        payload = point.get("payload") or {}
                        if workspace_id and str(payload.get("workspace_id")) != workspace_id:
                            continue
                        if doc_id and str(payload.get("document_id")) != doc_id:
                            continue
                        collection.pop(point_id, None)
                    return {"result": {"status": "acknowledged"}}
                if operation == "scroll" and method == "POST":
                    collection = self._memory_collections.setdefault(collection_name, {})
                    must = ((json_body or {}).get("filter") or {}).get("must") or []
                    workspace_id = _extract_filter_value(must, "workspace_id")
                    document_ids = _extract_filter_any(must, "document_id")
                    points = []
                    for point in collection.values():
                        payload = point.get("payload") or {}
                        if workspace_id and str(payload.get("workspace_id")) != workspace_id:
                            continue
                        if document_ids and str(payload.get("document_id")) not in document_ids:
                            continue
                        points.append(point)
                    return {"result": {"points": points, "next_page_offset": None}}
                if operation == "search" and method == "POST":
                    collection = self._memory_collections.setdefault(collection_name, {})
                    query_vector = (json_body or {}).get("vector") or []
                    limit = int((json_body or {}).get("limit") or 5)
                    must = ((json_body or {}).get("filter") or {}).get("must") or []
                    workspace_id = _extract_filter_value(must, "workspace_id")
                    document_ids = _extract_filter_any(must, "document_id")
                    scored = []
                    for point in collection.values():
                        payload = point.get("payload") or {}
                        if workspace_id and str(payload.get("workspace_id")) != workspace_id:
                            continue
                        if document_ids and str(payload.get("document_id")) not in document_ids:
                            continue
                        vector = point.get("vector") or []
                        score = _dense_cosine(query_vector, vector)
                        scored.append(
                            {
                                "id": point.get("id"),
                                "payload": payload,
                                "score": score,
                            }
                        )
                    scored.sort(key=lambda item: item["score"], reverse=True)
                    return {"result": scored[:limit]}
        raise QdrantCollectionServiceError(
            f"Unsupported in-memory Qdrant operation: {method} {path}"
        )


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _extract_filter_value(must: list[dict[str, Any]], key: str) -> str | None:
    for item in must:
        if item.get("key") != key:
            continue
        match = item.get("match") or {}
        value = match.get("value")
        if value is not None:
            return str(value)
    return None


def _extract_filter_any(must: list[dict[str, Any]], key: str) -> set[str]:
    for item in must:
        if item.get("key") != key:
            continue
        match = item.get("match") or {}
        values = match.get("any")
        if isinstance(values, list):
            return {str(value) for value in values}
    return set()


def _dense_cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(
        left_value * right_value for left_value, right_value in zip(left, right, strict=False)
    )
    if numerator == 0:
        return 0.0
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
