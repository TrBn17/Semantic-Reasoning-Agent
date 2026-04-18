# Phase 2 Start Notes

## Goal

Start Phase 2 with working backend contracts for document ingestion, retrieval, and citations without pretending the production data plane already exists.

## What this pass implements

- document upload endpoints
- Postgres-backed document persistence
- Celery-dispatched ingestion pipeline
- parser coverage for `pdf`, `docx`, and `xlsx`
- DB-backed chunk embedding and search
- citation composition for retrieval and chat
- reprocess and reindex endpoints

## Deliberate limits

- no MinIO yet
- no Qdrant yet
- no reranker yet
- no OCR fallback yet

## Why this shape

The repository is still at bootstrap stage. The current version moves state into a real relational store and moves ingestion off the request thread, while keeping retrieval on the database-backed chunk table until Qdrant is introduced.
