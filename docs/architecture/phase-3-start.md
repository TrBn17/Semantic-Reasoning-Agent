# Phase 3 Starter Notes

This pass adds the first real ontology backend slice without pretending the whole BRD is finished.

What is real now:

- build records, step records, candidate entity rows, candidate relation rows
- asynchronous ontology extraction through the existing Celery worker pattern
- review endpoints for entities and relations
- publish/version tables for a relational graph snapshot
- Neo4j sync for published ontology versions
- latest-graph read API for downstream UI work

What is intentionally deferred:

- full provider matrix for model-driven extraction prompts (current: optional Anthropic path)
- human merge tooling beyond approve/reject
- ontology diffing across versions

This slice keeps Phase 3 observable and testable while introducing production seams for:
- extractor ports (rule + LLM hybrid)
- runtime composition root used by API and worker
- vector/storage interfaces to prepare Qdrant/MinIO migration.
