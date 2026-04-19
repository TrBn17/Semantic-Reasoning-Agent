# Backend

Backend package for the Semantic Reasoning Agent platform.

This backend is not modeled as a chat-first application. It is the current implementation baseline for a tool-first, workflow-centric, ontology-guided runtime.

## Paths

- Package: `apps/backend/src/semantic_reasoning_agent`
- Tests: `apps/backend/tests`
- API entrypoint: `python apps/backend/serve.py`
- Worker entrypoint: `python apps/backend/worker/serve.py`

## Main Runtime Areas

- `core`: settings and dependency container
- `entrypoints`: FastAPI route adapters
- `services`: application services for conversations, retrieval, documents, ontology, profiles, and model config
- `workers`: Celery app and task wrappers
- `ports`: stable seams for parser, graph, object store, vector backend, secrets, and LLM adapters
- `infrastructure`: concrete adapters behind those ports
- `persistence`: database manager, SQLAlchemy models, repositories
- `domain`: contracts and ontology logic
- `tools`: early tool-layer foundations

## Current Implemented Flows

- chat/conversation handling
- document upload and processing
- retrieval search and citations
- ontology build, review, publish, and Neo4j projection
- Celery task dispatch for document and ontology jobs

## Local Run

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
.venv\Scripts\python.exe apps/backend/worker/serve.py
```
