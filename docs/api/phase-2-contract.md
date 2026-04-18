# Phase 2 API Contract Draft

## Document APIs

- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/jobs`
- `POST /api/v1/documents/{document_id}/reprocess`

## Retrieval APIs

- `POST /api/v1/retrieval/search`
- `POST /api/v1/retrieval/reindex`

## Chat integration

`POST /api/v1/chat/messages` now accepts:

- `use_retrieval`
- `workspace_id`
- `document_ids`
- `top_k`

and returns `citations` when retrieval is enabled.

## Current implementation note

The current retrieval engine is DB-backed and the ingestion path is worker-driven:

- upload persists metadata and binary content first
- the API returns the document in `uploaded` state
- Celery workers advance it through parsing and indexing
- clients are expected to poll `GET /api/v1/documents/{document_id}` or `.../jobs`

The contract is intended to survive the later swap to MinIO and Qdrant.
