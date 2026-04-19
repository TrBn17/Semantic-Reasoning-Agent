# Semantic Reasoning Agent

Semantic Reasoning Agent is a backend-first, tool-first, workflow-centric, ontology-guided agent platform.

This repository should not be described as a generic chat bot backend. Chat is only one entrypoint. The architectural center is:

- task interpretation
- workflow selection
- tool execution
- ontology grounding
- evidence normalization and review

## Architecture Summary

The current codebase is an upgrade baseline, not a greenfield rewrite. It preserves the working backend seams and evolves them toward a unified task runtime.

```text
Entrypoints
  -> FastAPI route adapters
  -> task interpretation and service routing
  -> tool/worker execution
  -> evidence + ontology review/publish flows
  -> persisted state in Postgres
  -> optional graph projection in Neo4j
```

Current operating model:

- tools are first-class execution primitives
- workflows are first-class execution plans
- ontology is a runtime semantic control layer, not just graph output
- deterministic workflows and agentic resolution are expected to coexist

## Current Backend Baseline

What is already implemented in this repository:

- FastAPI entrypoints for chat, conversations, documents, retrieval, ontology, agents, profiles, auth, and model routing
- Celery workers for document processing and ontology build processing
- Postgres as the current durable system of record
- optional Neo4j projection for published ontology graph reads
- DB-backed object storage and DB-backed chunk retrieval/vector seam
- parser stack for `pdf`, `docx`, and `xlsx` using `pypdf`, `python-docx`, and `openpyxl`
- rule/LLM-assisted ontology extraction path with review and publish flow

What is provisioned but still behind stable ports/contracts:

- MinIO for future blob/object storage
- Qdrant for future retrieval backend

## Service Topology

Local compose at the repo root provisions:

- `postgres`
- `redis`
- `neo4j`
- `minio`
- `qdrant`
- `api`
- `worker`
- `frontend`

The canonical local compose file is [`docker-compose.yml`](docker-compose.yml).

## Repository Layout

```text
/apps
  /backend
    /src/semantic_reasoning_agent
      /core            # settings, DI container
      /domain          # errors, ontology logic, runtime contracts
      /entrypoints     # FastAPI routers and request dependencies
      /infrastructure  # graph, parser, storage, vector, LLM adapters
      /persistence     # SQLAlchemy models, repositories, database manager
      /ports           # stable backend seams
      /schemas         # request/response schemas
      /services        # application services
      /tools           # tool-layer foundations
      /workers         # Celery app and task wrappers
    /tests
  /frontend

/docs
  /api
  /architecture
  /runbooks
```

## Current API Surface

Implemented API families today:

- `/api/v1/chat/*`
- `/api/v1/conversations/*`
- `/api/v1/documents/*`
- `/api/v1/retrieval/*`
- `/api/v1/ontology/*`
- `/api/v1/models/*`
- `/api/v1/agents/*`
- `/api/v1/agents/profiles/*`
- `/api/v1/auth/*`

Planned next control-plane additions from the backend architecture:

- `/api/v1/tasks/resolve`
- `/api/v1/workflows/*`
- `/api/v1/tools`
- `/api/v1/evidence/promotions`
- `/api/v1/artifacts/generate`
- `/api/v1/web/extract`
- `/api/v1/mcp/invoke`

## Local Setup

1. Create `.env` from `.env.example`.

Keep both host-run and container-run variables:

- `DATABASE_URL`, `CELERY_BROKER_URL`, `NEO4J_URI`, `MINIO_ENDPOINT`, `QDRANT_URL` are for running services on the host
- `*_DOCKER` variants are for the API/worker containers inside Docker

2. Start the full local stack:

```powershell
docker compose up -d
```

3. Or, if you want to run app processes on the host and infra in Docker only:

```powershell
docker compose up -d postgres redis neo4j minio qdrant
```

4. Install backend dependencies:

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev]
```

5. Run the API on the host:

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
```

6. Run the worker on the host:

```powershell
.venv\Scripts\python.exe apps/backend/worker/serve.py
```

7. Run the frontend on the host:

```powershell
cd apps/frontend
npm install
npm run dev
```

Endpoints:

- API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Neo4j Browser: `http://localhost:7474`
- MinIO Console: `http://localhost:9001`
- Qdrant: `http://localhost:6333`

## Development Notes

- Python package root: `apps/backend/src/semantic_reasoning_agent`
- Backend tests: `apps/backend/tests`
- Frontend app: `apps/frontend`
- CI currently runs `ruff`, `pytest`, and frontend build checks

Useful commands:

```powershell
.venv\Scripts\python.exe -m pytest apps/backend/tests
.venv\Scripts\python.exe -m ruff check apps/backend/src apps/backend/tests
cd apps/frontend
npm run build
```

## Near-Term Roadmap

The current repo state aligns with the backend architecture roadmap roughly as follows:

1. Preserve the current FastAPI + Celery + Postgres baseline and keep service seams stable.
2. Formalize parser, storage, retrieval, and tool contracts before forcing backend swaps.
3. Add task resolution, workflow registry, and tool runtime as first-class backend control planes.
4. Upgrade ontology from extraction-only flow to runtime semantic guidance for routing, normalization, and review.
5. Add MCP/web tooling and richer dynamic agentic execution without making chat the system core.

## Non-Goals

This repository is explicitly not centered around:

- a generic chat loop
- answer generation as the only terminal output
- query rewriting as the architectural backbone
- immediate mandatory migration to MinIO, Qdrant, or a new orchestration framework
