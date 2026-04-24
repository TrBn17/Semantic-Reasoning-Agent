# Semantic Reasoning Agent

Semantic Reasoning Agent is a backend-first, tool-first, workflow-centric, ontology-guided platform.

This is not a generic chatbot backend. Chat is only one entrypoint. The runtime center is:

- task interpretation
- workflow selection
- tool execution
- ontology grounding
- evidence assembly, sufficiency checks, and output routing

This README is the as-built runtime guide for the current codebase.

## Core Architecture

High-level runtime shape:

```text
Entrypoints (chat/tasks/documents/ontology/tools/workflows)
  -> service layer orchestration
  -> tool runtime + search-tools
  -> evidence normalization + output router
  -> persistence and worker execution
```

Execution model:

- tools are first-class execution primitives
- workflows are first-class execution plans
- ontology is both data output and runtime guidance
- deterministic flows and agentic flows coexist

## Main Runtime Flows

## 1) Chat and Task Resolution

Primary paths:

- `POST /api/v1/chat/messages` (chat entrypoint)
- `POST /api/v1/tasks/resolve` (public task-runtime entrypoint)

Core implementation:

- chat adapter: `apps/backend/src/semantic_reasoning_agent/services/chat_stream_service.py`
- task runtime: `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py`
- tool runtime: `apps/backend/src/semantic_reasoning_agent/services/tool_runtime.py`

Flow:

1. Resolve conversation runtime provider/model readiness.
2. Resolve workspace and active/default agent profile.
3. Resolve orchestration mode in this order:
   - request override
   - profile `orchestration_config`
   - settings default (`TASK_RUNTIME_ORCHESTRATION_MODE`)
4. Execute one of two paths:
   - `legacy_static_plan`: static plan from slot bindings (`rag`, `ontology_search`)
   - `react_two_agent`: LlamaIndex ReAct orchestrator (DocsAgent + GraphAgent)
5. Invoke tools via `ToolRuntime` and gather evidence/citations.
6. Run context assembly, sufficiency/conflict checks, output routing.
7. Persist runtime audit and return reply with citations and tool calls.

Current ReAct v1 mapping:

- DocsAgent -> `supersearch.docs`
- GraphAgent -> `supersearch.graph`

## 2) Document Ingestion and Extraction

Primary API family: `/api/v1/documents/*`

Core implementation:

- `apps/backend/src/semantic_reasoning_agent/documents/service.py`
- worker task: `apps/backend/src/semantic_reasoning_agent/workers/worker_tasks.py`

Ingestion modes:

- `ontology`
- `retrieval`
- `both` (default)

Pipeline jobs:

1. `convert_markdown`
2. `store_artifacts`
3. `build_chunks` (retrieval/both only)
4. `index_chunks` (retrieval/both only)

Details:

- conversion via `MarkdownConverterService`
- chunking via `MarkdownChunker`
- retrieval indexing via `RetrievalService`
- artifacts persisted to object store + metadata DB
- structured extraction supports heuristic or LLM-assisted extraction from markdown artifacts

## 3) Ontology Build, Review, Publish, Draft Editing

Primary API family: `/api/v1/ontology/*`

Core implementation:

- `apps/backend/src/semantic_reasoning_agent/services/ontology_service.py`
- worker task: `semantic_reasoning_agent.tasks.process_ontology_build`

Lifecycle:

1. create build
2. async build processing
3. candidate review (entities/relations)
4. publish version
5. optional graph draft edits and draft publish

Also supported:

- draft graph CRUD (nodes/relations/type definitions)
- publish preview
- graph snapshot projection

## 4) Search Tools (`supersearch.docs`, `supersearch.graph`)

Primary API family: `/api/v1/search-tools/*`

Core implementation:

- `apps/backend/src/semantic_reasoning_agent/services/search_tool_service.py`

Behavior:

- workspace-scoped config CRUD
- auto-provision system defaults per workspace:
  - docs default (`workspace_default_rag`)
  - graph default (`workspace_default_ontology_search`)
- docs search supports semantic, BM25, and hybrid fusion
- graph search supports semantic index, Graphiti path, and SQL fact fallback
- outputs normalized to unified `Evidence` contract

## 5) Tool Control Plane

Primary API family: `/api/v1/tools/*` (internal/admin)

Core implementation:

- registry: `apps/backend/src/semantic_reasoning_agent/services/tool_registry.py`
- runtime: `apps/backend/src/semantic_reasoning_agent/services/tool_runtime.py`
- routes: `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py`

Capabilities:

- list registered tool specs
- invoke tool directly with standard envelope
- timeout/error normalization
- trace metadata (`trace_id`, latency, status)

## 6) Workflows Control Plane

Primary API family: `/api/v1/workflows/*` (internal/admin)

Core implementation:

- routes: `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/workflows.py`
- registry service: `apps/backend/src/semantic_reasoning_agent/services/workflow_registry_service.py`

Notes:

- public integrations should use `POST /api/v1/tasks/resolve`
- direct workflow run endpoint is for internal/debug

## API Surface (Current)

Registered route families in `apps/backend/src/semantic_reasoning_agent/entrypoints/router.py`:

- `/api/v1/auth/*`
- `/api/v1/settings/*`
- `/api/v1/providers/*` (advanced discovery/debug)
- `/api/v1/conversations/*`
- `/api/v1/chat/*`
- `/api/v1/tasks/*`
- `/api/v1/workflows/*`
- `/api/v1/tools/*`
- `/api/v1/search-tools/*`
- `/api/v1/documents/*`
- `/api/v1/retrieval/*`
- `/api/v1/ontology/*`
- `/api/v1/agents/*`
- `/api/v1/agents/profiles/*`
- `/api/v1/agent-capabilities/*`
- `/api/v1/knowledge-packs/*`

## Data and Infrastructure Boundaries

Primary stores:

- Postgres: source-of-truth metadata, conversations, docs, jobs, chunks, ontology state, runtime audit
- Redis: Celery broker/result + ephemeral runtime support
- Neo4j/Graphiti: graph projection/search path
- MinIO: optional object storage backend
- Qdrant: optional vector backend

Local `docker compose` services:

- `postgres`
- `redis`
- `neo4j`
- `minio`
- `qdrant`
- `api`
- `worker`
- `frontend`

## Repository Layout

```text
/apps
  /backend
    /src/semantic_reasoning_agent
      /core
      /documents
      /domain
      /entrypoints
      /infrastructure
      /persistence
      /ports
      /schemas
      /services
      /tools
      /workers
    /tests
  /frontend
```

## Local Setup

1. Create `.env` from `.env.example`.
2. Start stack:

```powershell
docker compose up -d
```

3. Install backend deps:

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev]
```

4. Run backend API:

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
```

5. Run worker:

```powershell
.venv\Scripts\python.exe apps/backend/worker/serve.py
```

6. Run frontend:

```powershell
cd apps/frontend
npm install
npm run dev
```

Default endpoints:

- API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Neo4j Browser: `http://localhost:7474`
- MinIO Console: `http://localhost:9001`
- Qdrant: `http://localhost:6333`

## Development Commands

Backend:

```powershell
.venv\Scripts\python.exe -m pytest apps/backend/tests
.venv\Scripts\python.exe -m ruff check apps/backend/src apps/backend/tests
```

Frontend:

```powershell
cd apps/frontend
npm run lint
npm run typecheck
npm run build
```

## Notes on This Documentation

- This document reflects live code paths and registered routes.
- GitNexus was used to review runtime/process relationships, then validated against source files because GitNexus index can be stale vs HEAD.
