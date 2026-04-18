# Phase 3 API Contract Draft

## Ontology build APIs

- `POST /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds/{build_id}`
- `GET /api/v1/ontology/builds/{build_id}/entities`
- `GET /api/v1/ontology/builds/{build_id}/relations`

## Review and publish APIs

- `POST /api/v1/ontology/entities/{entity_id}/review`
- `POST /api/v1/ontology/relations/{relation_id}/review`
- `POST /api/v1/ontology/builds/{build_id}/publish`
- `GET /api/v1/ontology/graph`

## Current implementation note

The current Phase 3 backend is a starter slice built on the existing Postgres, Celery, and Neo4j stack:

- ontology builds are queued and processed asynchronously through Celery
- extraction is hybrid (`rule + optional LLM structured extractor`) and DB-backed
- candidate entities and relations enter a review queue with `pending_review`, `approved`, or `rejected`
- publish creates versioned ontology snapshots in relational tables and syncs the approved snapshot to Neo4j
- graph reads come from Neo4j when it is enabled
- Postgres remains the audit/review/version source of truth

When `NEO4J_ENABLED=false`, the API falls back to the relational snapshot for local test and degraded runtime scenarios.
