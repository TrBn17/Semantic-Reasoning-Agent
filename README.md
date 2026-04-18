# Semantic Reasoning Agent

This repository now has a production-oriented refactor baseline for `Phase 3 - Ontology AI Extraction & Graph Foundation`, with a hybrid ontology extractor path (rule + LLM) and staged app layout migration.

## What changed in this cleanup

- Removed the hardcoded Anthropic smoke script and replaced it with a proper backend skeleton.
- Added a safe `.env.example` and moved provider configuration into settings.
- Bootstrapped a FastAPI service layout for:
  - health checks
  - auth placeholder
  - conversation management
  - model catalog
  - chat request handling
- Added a Phase 2 starter for:
  - `pdf/docx/xlsx` upload
  - DB-backed persistence for documents, jobs, and chunks
  - Celery-backed ingestion dispatch
  - retrieval search
  - citations in chat responses
- Added docs and tests to make the next implementation pass more structured.
- Added a Phase 3 ontology starter with:
  - candidate entity and relation extraction
  - review and publish APIs
  - versioned relational ontology snapshots
  - Neo4j sync for the published graph

## Repository layout (current target)

```text
/apps
  /backend            # FastAPI + Celery (`src/semantic_reasoning_agent`, tests, serve.py, worker/)
  /frontend           # Next.js UI
  /frontend-nextjs    # legacy placeholder
  /worker-celery      # legacy placeholder

/docs
  /api
  /architecture
  /runbooks
  /product
```

## Quick start

1. Create a local environment file from `.env.example`.

Set `POSTGRES_PASSWORD` to a strong value. Keep `DATABASE_URL` for host-run API/worker and `DATABASE_URL_DOCKER` for docker-compose API/worker containers.

1. Start infrastructure services:

```powershell
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis neo4j
```

1. Install backend dependencies:

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev]
```

1. Run API:

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
```

1. Run worker:

```powershell
.venv\Scripts\python.exe apps/backend/worker/serve.py
```

1. Run frontend:

```powershell
cd apps/frontend
npm install
npm run dev
```

## Current scope

This is still not a complete production delivery. Current scope includes:

- domain models
- settings
- provider adapter contracts
- Postgres-backed conversation and document storage
- structured parsers for `pdf/docx/xlsx`
- Celery-dispatched ingestion jobs
- DB-backed retrieval and citation composition behind a vector backend port
- versioned ontology review and publish flows
- Neo4j-backed published graph sync
- hybrid ontology extraction seam (rule extractor + optional LLM structured extractor)
- app container composition for API and worker
- API contracts and smoke tests

## Next implementation steps

1. Replace the DB-backed local chunk search with Qdrant.
2. Move document binary storage from Postgres blobs to MinIO.
3. Add ontology merge flows, version diffing, and richer extraction prompts.
4. Implement real provider adapters and streamed grounded responses.
5. Add Langfuse tracing and token usage persistence.
