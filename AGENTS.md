# AGENTS Guide (Current Architecture)

Tai lieu nay la **nguon su that cho Agent** khi lam viec trong repo `Semantic-Reasoning-Agent`.
Muc tieu la phan anh **trang thai dang chay thuc te** cua codebase, khong mo ta roadmap cu.

---

## 1) Project Identity

`Semantic-Reasoning-Agent` la nen tang:

- **backend-first**
- **tool-first**
- **workflow-centric**
- **ontology-guided**

Chat la entrypoint quan trong, nhung **khong phai kien truc trung tam**.
Trung tam runtime hien tai:

- task resolution (`/api/v1/tasks/resolve`)
- tool runtime (`ToolRegistry` + `ToolRuntime`)
- ontology grounding + evidence routing
- document/ontology processing pipelines (Celery jobs)

---

## 2) Tech Stack (As-Built)

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- Celery
- Pydantic v2 (`pydantic-settings`)
- LLM providers: OpenAI, Anthropic, Gemini, Ollama, OpenRouter
- Graph layer: Neo4j + Graphiti gateway
- Storage: Postgres blob store (default), MinIO (optional via port)
- Retrieval index: Postgres vector seam (default), Qdrant backend path (optional)

### Frontend

- Next.js 15
- React 19 + TypeScript
- Tailwind + Radix/shadcn UI
- TanStack Query + Zustand
- i18n (`react-i18next`, EN/VI)

### Local Infra (`docker-compose.yml`)

- `postgres`
- `redis`
- `neo4j`
- `minio`
- `qdrant`
- `api`
- `worker`
- `frontend`

---

## 3) Canonical Source Layout

### Backend package root

`apps/backend/src/semantic_reasoning_agent`

- `core`: settings + DI container
- `entrypoints`: FastAPI routers
- `services`: application/runtime services
- `documents`: conversion + chunking + ingestion orchestration
- `domain`: contracts + ontology domain logic
- `tools`: tool implementations and schemas
- `infrastructure`: adapters (LLM, graphiti, storage, ontology extraction)
- `persistence`: DB manager + ORM models
- `workers`: Celery app + async job tasks
- `ports`: interface seams for infra adapters

### Frontend

`apps/frontend/src`

- `app`: routes/pages (`ask`, `documents`, `ontology`, `graph`, `settings`, `agents`, `tasks`, `tools`, `search-tools`, ...)
- `components`: feature UI blocks
- `shared/api`: typed API clients mapping backend schemas
- `shared/query`, `shared/layout`, `shared/i18n`: app runtime utilities

---

## 4) API Surface (Current)

Router dang ky o `entrypoints/router.py`:

- `/api/v1/auth/*`
- `/api/v1/settings/*`
- `/api/v1/providers/*` (internal/advanced discovery)
- `/api/v1/conversations/*`
- `/api/v1/chat/*`
- `/api/v1/tasks/*`
- `/api/v1/workflows/*`
- `/api/v1/tools/*` (internal/admin control plane)
- `/api/v1/search-tools/*`
- `/api/v1/documents/*`
- `/api/v1/retrieval/*`
- `/api/v1/ontology/*`
- `/api/v1/agents/*`
- `/api/v1/agents/profiles/*`
- `/api/v1/agent-capabilities/*`
- `/api/v1/knowledge-packs/*`

Luu y:

- Public entrypoint cho task runtime: `POST /api/v1/tasks/resolve`
- `POST /api/v1/workflows/{id}/run` la internal/debug
- `GET /api/v1/tools` va `POST /api/v1/tools/{tool_name}/invoke` la internal/admin
- `POST /api/v1/search-tools/{config_id}/duplicate` dung de nhan ban system/default search tool thanh custom tool

---

## 5) Runtime Flows (Current Truth)

### 5.1 Chat / Task Resolution Flow

1. `POST /chat/messages` vao `ChatStreamService`.
2. Resolve model/provider readiness qua `ModelConfigService`.
3. Append user message vao conversation.
4. Goi `TaskRuntimeService.resolve_chat_request(...)`.
5. Trong `TaskRuntimeService`:
   - interpret task
   - ontology grounding
   - workflow select
   - build tool plan theo `agent_profiles.tool_assignments`, capability guardrails, va document scope
   - validate plan qua `AgenticLoopService`
   - invoke tools qua `ToolRuntime` (tuan thu `ToolEnvelope`/`ToolResult`)
   - assemble evidence + citations
   - sufficiency check (`EvidenceJudge`) + conflict analysis (`ConflictEngine`)
   - output routing (`OutputRouter`)
   - fallback sang model-only answer neu policy cho phep
6. Assistant response duoc append vao conversation va tra ve API (kem citations + tool_calls).

Tool planning chat runtime co the su dung:

- `supersearch.docs` qua slot `rag`
- `supersearch.graph` qua slot `ontology_search`
- internal tools nhu `retrieval.internal` / `ontology.lookup` / `graphiti.search` van ton tai trong registry nhung khong con la flow gan tool chinh cho agent profile

Theo:

- slot bindings luu trong `agent_profiles.tool_assignments`
- capability preset/profile policy
- allowed/blocked tools
- selected document scope (request + knowledge packs)
- evidence source policy

Quy tac quan trong:

- `tool instance` la don vi gan thuc te, khong phai `tool family`
- v1 co 2 slot chinh: `rag` va `ontology_search`
- neu slot trong, runtime khong fallback ngam ve search tool mac dinh cu
- `ConversationResponse` expose `effective_tool_bindings`, khong chi `effective_tool_names`

### 5.2 Document Ingestion Flow

`DocumentService` la orchestrator chinh.

Ingestion modes:

- `ontology`
- `retrieval`
- `both` (default)

Pipeline jobs:

1. `convert_markdown`
2. `store_artifacts`
3. `build_chunks` (chi khi mode = `retrieval` hoac `both`)
4. `index_chunks` (chi khi mode = `retrieval` hoac `both`)

Conversion + chunking:

- Converter chinh: `MarkdownConverterService`
- Native converters cho `pdf`, `docx`, `xlsx`, `csv`, text-like formats
- Fallback converter: `markitdown`
- Chunking: `MarkdownChunker`
- Artifacts luu object store + metadata DB (`markdown`, `normalized_json`)
- `document_chunks` luu embedding payload cung metadata `embedding_provider` / `embedding_model`

Structured extraction (`POST /documents/{id}/extract`):

- doc markdown artifact
- heuristic extraction hoac LLM extraction (neu provider/model ready)
- luu `DocumentExtractionRun`

### 5.3 Ontology Build / Review / Publish Flow

`OntologyService` xu ly toan bo vong doi ontology.

Build creation:

- `POST /ontology/builds`
- document phai o trang thai `indexed`
- bat buoc `extraction_provider` + `extraction_model`
- enqueue Celery task

Async build processing:

- Worker chay `process_ontology_build_task` -> `OntologyService.process_build`
- Steps tracked trong DB:
  1. `classify_document_domain`
  2. `extract_entities`
  3. `extract_relations`
  4. `resolve_entities`
  5. `build_graph_upsert_plan`
  6. `sync_neo4j`

Review + publish:

- Review candidate entities/relations
- Publish build: `POST /ontology/builds/{id}/publish`
- Preview publish: `GET /ontology/builds/{id}/publish-preview`
- Published snapshot day qua `OntologyGraphPublisher` (Graphiti/Neo4j path)

Draft graph editing:

- `GET /ontology/graph/draft`
- CRUD draft nodes/relations
- update entity/relation type drafts
- reset/publish draft

### 5.4 Search Tools Flow (Saved Super Search)

`SearchToolConfigService` cung cap:

- search tool theo model `tool instance`, workspace-scoped cho `docs` va `graph`
- CRUD configs voi explicit `embedding_provider` / `embedding_model`
- system-managed defaults duoc auto-provision per workspace:
  - `workspace_default_rag` -> `docs`
  - `workspace_default_ontology_search` -> `graph`
- readiness validation dua tren embedding backend readiness thuc te, khong chi metadata check
- run config:
  - docs: semantic retrieval tren embedding index + optional BM25/fusion
  - graph: ontology semantic index truoc, roi moi den graphiti/sql-facts routing
- output normalized Evidence shape

Workspace search defaults:

- settings luu `embedding_provider` va `embedding_model` mac dinh cho workspace
- mac dinh local hien tai dung Cloudflare embeddings tu env neu workspace chua override
- tool config cu van duoc doc/backfill qua field legacy `provider` / `model`

Frontend flow:

- trang `agents` la luong chinh de gan 2 slot tool
- trang `search-tools` la luong nang cao de xem, duplicate, va tuy chinh tool instance
- system tools co badge/lock ro rang va khong cho mutate truc tiep

### 5.5 Tool Control Plane Flow

`/api/v1/tools` dung cho internal/admin:

- list registry metadata (`ToolSpec`)
- invoke tool truc tiep bang standard envelope

Registry build tai `core/container.py` qua `build_tool_registry(...)`.
Tools co the register (tuy dependency san sang):

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search`
- `graphiti.ingest_episode`
- `supersearch.docs`
- `supersearch.graph`

---

## 6) Worker Model

Celery app o `workers/celery_app.py`, tasks o `workers/worker_tasks.py`.

Hai background jobs chinh:

- `semantic_reasoning_agent.tasks.process_document`
- `semantic_reasoning_agent.tasks.process_ontology_build`

Dispatcher path: services goi `TaskDispatcher`, khong goi task truc tiep.

Search index notes:

- document chunk embeddings duoc tao trong retrieval/index path bang `EmbeddingService`
- ontology semantic index hien duoc ensure/rebuild boi `SearchToolConfigService` khi provision/run graph search tool, chua la Celery flow rieng

---

## 7) Data Boundaries (Current)

- **Postgres**: source-of-truth cho metadata, conversations, docs, chunks, ontology review/publish state, runtime audit
- **Postgres** cung luu `workspace_search_settings`, `search_tool_configs`, `document_chunks` embeddings, va `ontology_search_index`
- **Redis**: Celery broker/result backend + ephemeral runtime support
- **Neo4j/Graphiti**: graph runtime/projection path
- **MinIO**: object-store backend optional (`OBJECT_STORE_BACKEND`)
- **Qdrant**: vector backend optional (`VECTOR_STORE_BACKEND`)

Mac dinh local hien tai van co duong Postgres object + retrieval, khong bat buoc migrate ngay.

---

## 8) Legacy Removal Notes (Important)

Khi update code/doc, **khong quay lai narrative cu**:

- Khong mo ta project la "chatbot backend thuan chat".
- Khong coi parser registry cu (`documents/parsers/*`) la active path.
  - Path ingestion hien tai: `documents/converters/markdown_converter.py` + `documents/chunking.py`.
- Khong coi `/tools`, `/tasks`, `/workflows` la "planned-only".
  - Chung da co route runtime trong code.
- Khong coi ontology graph la output phu.
  - Ontology runtime + review/publish + draft editing la luong chinh.

---

## 9) Agent Working Checklist

Truoc khi sua code:

1. Xac dinh dung module owner:
   - documents -> `documents/*`, `services/retrieval_service.py`, worker task
   - task runtime -> `services/task_runtime.py`, `services/*_engine.py`, `tools/*`
   - ontology -> `services/ontology_service.py`, `infrastructure/ontology/*`, `schemas/ontology.py`
   - API surface -> `entrypoints/v1/*` + `schemas/*`
2. Neu sua API contract, cap nhat frontend `shared/api/*` va `shared/api/types.ts`.
3. Neu them/sua background flow, verify queue path qua `TaskDispatcher` + `worker_tasks.py`.
4. Khong de endpoint "planned" trong docs neu route da ton tai hoac da bi xoa.
5. Neu sua search tools / agent runtime, keep nhat quan 4 lop:
   - `settings` workspace embedding defaults
   - `search-tools` tool-instance contracts
   - `agent_profiles.tool_assignments` slot-based bindings
   - `conversation/chat` effective binding payloads

Sau khi sua code:

1. Chay tests lien quan backend/frontend.
2. Confirm lint/typecheck pass.
3. Cap nhat tai lieu lien quan (`README.md`, `apps/backend/README.md`, `apps/frontend/README.md`) neu contract thay doi.
4. Khong tai dua vao implicit fallback khi doc/code docs ve agent tool assignment.

---

## 10) Useful Commands

```powershell
# Infra + app stack
docker compose up -d

# Backend
.venv\Scripts\python.exe -m pytest apps/backend/tests
.venv\Scripts\python.exe -m ruff check apps/backend/src apps/backend/tests
.venv\Scripts\python.exe apps/backend/serve.py
.venv\Scripts\python.exe apps/backend/worker/serve.py

# Frontend
cd apps/frontend
npm install
npm run dev
npm run build
npm run lint
npm run typecheck
```

---

## 11) Quick Mental Model For New Agents

Neu ban moi vao repo, dung model nay:

- Conversation/chat chi la UI-entrypoint.
- Public runtime entrypoint la `tasks/resolve`.
- Tool runtime + evidence contracts la "spine" cua system.
- Document ingestion tao markdown artifacts; retrieval branch optional theo mode.
- Ontology co full lifecycle: build -> review -> publish -> graph/draft.
- Search-tools la `tool instance` workspace-scoped, co 2 default system tools va embedding defaults theo workspace.
- Agent profile gan tool qua 2 slot `rag` va `ontology_search`; khong co implicit fallback neu chua gan slot.

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Semantic-Reasoning-Agent** (8182 symbols, 19473 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Semantic-Reasoning-Agent/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Semantic-Reasoning-Agent/clusters` | All functional areas |
| `gitnexus://repo/Semantic-Reasoning-Agent/processes` | All execution flows |
| `gitnexus://repo/Semantic-Reasoning-Agent/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
# AGENTS Guide (Current Architecture)

Tài liệu này là **nguồn sự thật cho Agent** khi làm việc trong repo `Semantic-Reasoning-Agent`.
Mục tiêu là phản ánh **trạng thái đang chạy thực tế** của codebase, không mô tả roadmap cũ.

---

## 1) Project Identity

`Semantic-Reasoning-Agent` là một nền tảng:

- **backend-first**
- **tool-first**
- **workflow-centric**
- **ontology-guided**

Chat là entrypoint quan trọng, nhưng **không phải kiến trúc trung tâm**.
Trung tâm runtime hiện tại là:

- task resolution (`/api/v1/tasks/resolve`)
- tool runtime (`ToolRegistry` + `ToolRuntime`)
- ontology grounding + evidence routing
- document/ontology processing pipelines (Celery jobs)

---

## 2) Tech Stack (As-Built)

### Backend

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- Celery
- Pydantic v2 (`pydantic-settings`)
- LLM providers: OpenAI, Anthropic, Gemini, Ollama, OpenRouter (qua settings/adapters)
- Graph layer: Neo4j + Graphiti gateway
- Storage: Postgres blob store (default), MinIO (optional via port)
- Retrieval index: Postgres vector seam (default), Qdrant backend path (optional)

### Frontend

- Next.js 15
- React 19 + TypeScript
- Tailwind + Radix/shadcn UI
- TanStack Query + Zustand
- i18n (`react-i18next`, EN/VI)

### Local Infra (`docker-compose.yml`)

- `postgres`
- `redis`
- `neo4j`
- `minio`
- `qdrant`
- `api`
- `worker`
- `frontend`

---

## 3) Canonical Source Layout

### Backend package root

`apps/backend/src/semantic_reasoning_agent`

- `core`: settings + DI container
- `entrypoints`: FastAPI routers
- `services`: application/runtime services
- `documents`: conversion + chunking + ingestion orchestration
- `domain`: contracts + ontology domain logic
- `tools`: tool implementations and schemas
- `infrastructure`: adapters (LLM, graphiti, storage, ontology extraction)
- `persistence`: DB manager + ORM models
- `workers`: Celery app + async job tasks
- `ports`: interface seams for infra adapters

### Frontend

`apps/frontend/src`

- `app`: routes/pages (`ask`, `documents`, `ontology`, `graph`, `settings`, `agents`, `tasks`, `tools`, `search-tools`, ...)
- `components`: feature UI blocks
- `shared/api`: typed API clients mapping backend schemas
- `shared/query`, `shared/layout`, `shared/i18n`: app runtime utilities

---

## 4) API Surface (Current)

Router đăng ký ở `entrypoints/router.py`:

- `/api/v1/auth/*`
- `/api/v1/settings/*`
- `/api/v1/providers/*` (internal/advanced discovery)
- `/api/v1/conversations/*`
- `/api/v1/chat/*`
- `/api/v1/tasks/*`
- `/api/v1/workflows/*`
- `/api/v1/tools/*` (internal/admin control plane)
- `/api/v1/search-tools/*`
- `/api/v1/documents/*`
- `/api/v1/retrieval/*`
- `/api/v1/ontology/*`
- `/api/v1/agents/*`
- `/api/v1/agents/profiles/*`
- `/api/v1/agent-capabilities/*`
- `/api/v1/knowledge-packs/*`

Luu y:

- Public entrypoint cho task runtime: `POST /api/v1/tasks/resolve`
- `POST /api/v1/workflows/{id}/run` la internal/debug
- `GET /api/v1/tools` va `POST /api/v1/tools/{tool_name}/invoke` la internal/admin

---

## 5) Runtime Flows (Current Truth)

## 5.1 Chat / Task Resolution Flow

1. `POST /chat/messages` vao `ChatStreamService`.
2. Resolve model/provider readiness qua `ModelConfigService`.
3. Append user message vao conversation.
4. Gọi `TaskRuntimeService.resolve_chat_request(...)`.
5. Trong `TaskRuntimeService`:
   - interpret task
   - ontology grounding
   - workflow select
   - build tool plan theo profile/capability/document scope
   - validate plan qua `AgenticLoopService`
   - invoke tools qua `ToolRuntime` (tuan thu `ToolEnvelope`/`ToolResult`)
   - assemble evidence + citations
   - sufficiency check (`EvidenceJudge`) + conflict analysis (`ConflictEngine`)
   - output routing (`OutputRouter`)
   - fallback sang model-only answer neu policy cho phep
6. Assistant response duoc append vao conversation va tra ve cho API (kem citations + tool_calls).

### Tool planning hiện tại (chat runtime)

Co the su dung:

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search`

Tuy theo:

- capability preset/profile policy
- allowed/blocked tools
- selected document scope (request + knowledge packs)
- evidence source policy

## 5.2 Document Ingestion Flow

`DocumentService` la orchestrator chính.

### Ingestion modes

- `ontology`
- `retrieval`
- `both` (default)

### Pipeline jobs

Base jobs:

1. `convert_markdown`
2. `store_artifacts`

Retrieval-only jobs (khi mode = `retrieval` hoac `both`):

3. `build_chunks`
4. `index_chunks`

### Conversion + chunking model

- Converter chính: `MarkdownConverterService`
- Native converters cho: `pdf`, `docx`, `xlsx`, `csv`, text-like formats
- Fallback converter: `markitdown`
- Chunking: `MarkdownChunker`
- Artifacts luu object store + metadata DB (`markdown`, `normalized_json`)

### Structured extraction

`POST /documents/{id}/extract`:

- đọc markdown artifact
- heuristic extraction hoac LLM extraction (neu provider/model ready)
- lưu `DocumentExtractionRun`

## 5.3 Ontology Build / Review / Publish Flow

`OntologyService` xử lý toàn bộ vòng đời ontology:

### Build creation

- `POST /ontology/builds`
- yeu cau document da `indexed`
- yeu cau explicit `extraction_provider` + `extraction_model`
- enqueue Celery task

### Async build processing

Celery worker chạy `process_ontology_build_task` -> `OntologyService.process_build`.

Pipeline steps (tracked in DB):

1. `classify_document_domain`
2. `extract_entities`
3. `extract_relations`
4. `resolve_entities`
5. `build_graph_upsert_plan`
6. `sync_neo4j`

### Review + publish

- Review candidate entities/relations
- Publish build: `POST /ontology/builds/{id}/publish`
- Preview publish: `GET /ontology/builds/{id}/publish-preview`
- Published snapshot đẩy qua `OntologyGraphPublisher` (Graphiti/Neo4j path)

### Draft graph editing

Co draft APIs:

- `GET /ontology/graph/draft`
- CRUD draft nodes/relations
- update entity/relation type drafts
- reset/publish draft

## 5.4 Search Tools Flow (Saved Super Search)

`SearchToolConfigService` cung cap:

- CRUD configs cho `docs` va `graph`
- readiness validation theo provider/model
- run config:
  - docs: semantic + optional BM25 + fusion
  - graph: graphiti/sql-facts/hybrid path (tu routing)
- output normalised Evidence shape

## 5.5 Tool Control Plane Flow

`/api/v1/tools` dung cho internal/admin:

- list registry metadata (`ToolSpec`)
- invoke tool trực tiếp bằng standard envelope

Registry build tại `core/container.py` qua `build_tool_registry(...)`.
Các tool có thể được register tùy dependency sẵn sàng:

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search`
- `graphiti.ingest_episode`
- `supersearch.docs`
- `supersearch.graph`

---

## 6) Worker Model

Celery app ở `workers/celery_app.py`, tasks ở `workers/worker_tasks.py`.

Hai background jobs chính:

- `semantic_reasoning_agent.tasks.process_document`
- `semantic_reasoning_agent.tasks.process_ontology_build`

Dispatcher: `services` gọi `TaskDispatcher`, không gọi task trực tiếp.

---

## 7) Data Boundaries (Current)

- **Postgres**: source-of-truth cho metadata, conversations, docs, chunks, ontology review/publish state, runtime audit
- **Redis**: Celery broker/result backend + ephemeral runtime support
- **Neo4j/Graphiti**: graph runtime/projection path
- **MinIO**: object-store backend optional (qua `OBJECT_STORE_BACKEND`)
- **Qdrant**: vector backend optional (qua `VECTOR_STORE_BACKEND`)

Mac dinh local hien tai van co duong Postgres object + retrieval khong bat buoc migrates ngay.

---

## 8) Legacy Removal Notes (Important)

Khi update code/doc, **khong quay lai narrative cu** sau:

- Khong mo ta project la "chatbot backend thuan chat".
- Khong coi parser registry cu (`documents/parsers/*`) la active path.
  - Path ingestion hien tai: `documents/converters/markdown_converter.py` + `documents/chunking.py`.
- Khong coi `/tools`, `/tasks`, `/workflows` la "planned-only".
  - Chung da co route runtime trong code.
- Khong coi ontology graph la output phu.
  - Ontology runtime + review/publish + draft editing dang la luong chinh.

---

## 9) Agent Working Checklist

Truoc khi sua code:

1. Xac dinh dung module owner:
   - documents -> `documents/*`, `services/retrieval_service.py`, worker task
   - task runtime -> `services/task_runtime.py`, `services/*_engine.py`, `tools/*`
   - ontology -> `services/ontology_service.py`, `infrastructure/ontology/*`, `schemas/ontology.py`
   - API surface -> `entrypoints/v1/*` + `schemas/*`
2. Neu sua contract API, cap nhat frontend `shared/api/*` va `shared/api/types.ts`.
3. Neu them/sua background flow, verify queue path qua `TaskDispatcher` + `worker_tasks.py`.
4. Khong de "planned endpoint" trong docs neu route da ton tai hoac da bi xoa.

Sau khi sua code:

1. Chay tests lien quan backend/frontend.
2. Confirm lint/typecheck pass.
3. Cap nhat tai lieu co lien quan (`README.md`, `apps/backend/README.md`, `apps/frontend/README.md`) neu contract thay doi.

---

## 10) Useful Commands

```powershell
# Infra + app stack
docker compose up -d

# Backend
.venv\Scripts\python.exe -m pytest apps/backend/tests
.venv\Scripts\python.exe -m ruff check apps/backend/src apps/backend/tests
.venv\Scripts\python.exe apps/backend/serve.py
.venv\Scripts\python.exe apps/backend/worker/serve.py

# Frontend
cd apps/frontend
npm install
npm run dev
npm run build
npm run lint
npm run typecheck
```

---

## 11) Quick Mental Model For New Agents

Neu ban moi vao repo, dung model nay:

- Conversation/chat chi la UI-entrypoint.
- Public runtime entrypoint la `tasks/resolve`.
- Tool runtime + evidence contracts la "spine" cua system.
- Document ingestion tao markdown artifacts; retrieval branch la optional theo mode.
- Ontology co full lifecycle: build -> review -> publish -> graph/draft.
- Search-tools la lop cau hinh/rerank bo sung cho retrieval+graph.

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Semantic-Reasoning-Agent** (8182 symbols, 19473 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Semantic-Reasoning-Agent/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Semantic-Reasoning-Agent/clusters` | All functional areas |
| `gitnexus://repo/Semantic-Reasoning-Agent/processes` | All execution flows |
| `gitnexus://repo/Semantic-Reasoning-Agent/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
# Technical PRD v2.1 (Upgrade Blueprint, Backend-First)
## Tool-First, Workflow-Centric, Ontology-Guided Backend Agent Platform

**Status:** Draft for implementation  
**Audience:** Backend engineers and AI coding agents  
**Purpose:** Define the upgrade path from the current backend into a tool-first runtime where workflows and ontology guide execution. This document is implementation-oriented and contract-focused.

---

## 1. Executive Summary

This system must not be described as a generic chat agent backend.

It is a **tool-first, workflow-centric, ontology-guided backend agent platform** where:

- **tools** are the first-class execution primitives,
- **workflows** are the first-class execution plans,
- **ontology** is the semantic control layer for runtime grounding, policy, normalization, and review,
- **chat is only one entrypoint**, not the architectural center.

The current codebase already provides a real backend baseline:

- FastAPI API routes for chat, documents, retrieval, ontology, and model routing
- Celery workers for document ingestion and ontology build jobs
- PostgreSQL as the current durable system of record
- optional Neo4j sync and graph read path
- DB-backed object storage and DB-backed chunk retrieval
- PDF parsing through a parser registry with `marker` preferred for PDF and `pypdf` fast-mode fallback, DOCX parsing with `python-docx`, XLSX parsing with `openpyxl`, CSV parsing with stdlib `csv`

This PRD defines the **next upgrade step**, not a greenfield rewrite. The upgrade should preserve current service seams and evolve them into a unified task runtime.

Core outcome:

- a runtime that resolves tasks through tools and workflows,
- guided by ontology,
- with outputs that may be an answer, ontology candidates, review work, graph updates, promoted evidence, or generated artifacts.

---

## 2. Scope Backend v1

Backend v1 in this upgrade includes:

- task interpretation and workflow selection over the current FastAPI + service layer
- tool registry and tool execution envelopes
- deterministic workflows for ingestion, indexing, ontology build, review, publish, and artifact jobs
- dynamic agentic flow for ambiguous, multi-step, or multi-source tasks
- ontology-guided tool selection, evidence normalization, and review routing
- retrieval modes for internal, live web, and hybrid evidence gathering
- stable storage and provenance contracts across Postgres, Neo4j, Redis, MinIO, and Qdrant

Current baseline that must be preserved:

- Postgres-backed document metadata, chunks, jobs, ontology review, and version state
- Celery-dispatched document and ontology workers
- current parser stack: `marker` preferred for PDF via optional extra, `pypdf` fallback for fast PDF mode, `python-docx`, `openpyxl`, stdlib `csv`
- current optional graph projection to Neo4j

Near-term additions allowed without architectural churn:

- add `PyMuPDF` as a PDF parser backend behind the parser contract if the team standardizes on it
- add MinIO and Qdrant as replaceable backends behind stable storage and retrieval ports
- add web extract and MCP as tool families, not as separate architectural silos

Out of scope for this upgrade step:

- making chat or answer generation the system center
- forcing a full parser stack migration before contracts are stable
- forcing Qdrant, MinIO, or LangGraph adoption before the runtime seams exist
- full semantic-web reasoning or academic OWL-heavy inference

---

## 2.5 Current Implementation Status

**Last updated:** 2026-04-20 — after backend Phase-3 groundwork (PR-1 → PR-3).

### Shipped

- **§9 Tool Registry Model** — `ToolSpec` dataclass + `ToolRegistry` service at
  `apps/backend/src/semantic_reasoning_agent/services/tool_registry.py`. Registry
  lookup by name, filter by family + risk ceiling.
- **§9 Standard Tool Input / Output** — `ToolEnvelope` (with `call_id`, `task_type`,
  `task_payload`, `OntologyContextRef`, `ToolConstraints`, `workflow_id`) and
  `ToolResult` (with `started_at`, `finished_at`, `latency_ms`, `evidence`,
  `artifacts`, `state_patch`, `next_action_hints`, `ToolMeta`) at
  `domain/contracts/tool_envelope.py`.
- **§9 Unified Evidence Contract** — `Evidence` + typed `CitationAnchor`
  (`anchor_type`, `label`, `locator`) + typed `Provenance` at
  `domain/contracts/evidence.py`.
- **Native function-calling adapters** — `AnthropicAdapter` (messages.create with
  `tool_use` / `tool_result` blocks) and `OpenAIAdapter` (chat.completions with
  function tool calls) under `infrastructure/llm/`, sharing a unified
  `LLMMessage` / `LLMToolCall` / `LLMResponse` envelope at
  `domain/contracts/llm.py`. `EchoAdapter` keeps the test path working.
- **ToolRuntime** — `services/tool_runtime.py`: timeout via ThreadPoolExecutor,
  exception wrapping into `failed` result, latency measurement, `trace_id`
  stamping, `tool_call_id` propagation into each evidence's provenance.
- **Concrete tools (Phase-3 scope)** — `retrieval.internal` (wraps
  `RetrievalService.search`, maps per-chunk results to §9 Evidence with page /
  section / sheet-row anchors) and `ontology.lookup` (wraps
  `OntologyService.get_graph`, emits `graph_node` + `graph_edge` Evidence from
  the current published ontology version — no hardcoded type names, emergent
  schema only).
- **API endpoints** — `GET /api/v1/tools` (list registered specs, filterable by
  family / max_risk) and `POST /api/v1/tools/{tool_name}/invoke` (admin-facing
  execution with the full §9 input/output envelopes).
- **Integration verified** — end-to-end test uploads a PDF, invokes
  `retrieval.internal`, and asserts every §9 Evidence field is populated.

### Not yet implemented (deferred)

- **Task runtime** — `TaskInterpreter`, `OntologyGrounding`,
  `WorkflowSelector`, `AgenticLoop`. The LLM still runs single-shot inside
  `chat_stream_service.ChatStreamService.send_message` with `tools=()`. Chat
  has native function calling machinery wired underneath but no tool execution
  loop yet.
- **Workflows** — no `WorkflowRegistry`, no `/api/v1/workflows*`,
  no `/api/v1/tasks/resolve`. Document ingestion and ontology build still run
  on Celery as deterministic Celery tasks, not as workflow runtime entries.
- **Additional tool families** — `web.extract`, `mcp.invoke`,
  `evidence.promote`, `artifact.generate`, `graph.publish` not yet registered.
  These are the Phase 5 + Phase 6 targets.
- **Sufficiency / conflict checks** — §9 steps 7-8 (sufficiency gate, conflict
  merge) are out-of-scope for the current shipment and belong with the agentic
  loop work.
- **Durable persistence of tool calls and evidence** — `ToolResult` /
  `Evidence` exist only within a request lifecycle. No `task_runs`,
  `tool_calls`, or `evidence_promotions` tables yet.
- **Streaming tool calls** — adapters return complete `LLMResponse` only; SSE
  tokenwise streaming with partial-JSON accumulation is deferred.
- **Gemini adapter** — `google-genai` SDK is installed but no adapter.
- **Runtime framework choice (LangGraph / DeepAgents)** — framework adoption
  is still out-of-scope per §2; the current contracts are framework-agnostic so
  PR-4 can slot either in without changing §9 boundaries.

---

## 3. Core Architectural Principles

1. **Tool-first, not chat-first**  
   Runtime behavior is organized around tools and task execution, not around a chat loop.

2. **Workflow-centric**  
   Workflows are named, versioned execution plans with typed inputs, outputs, and policy.

3. **Ontology-guided**  
   Ontology is not just graph output. It is a semantic control layer for task interpretation, tool selection, evidence normalization, review, and graph publishing.

4. **Chat is one entrypoint**  
   Other entrypoints include document ingestion, ontology review, graph publish, admin actions, scheduled jobs, and artifact generation.

5. **Deterministic and agentic flows coexist**  
   Deterministic workflows handle bounded backend pipelines. Dynamic agentic flow handles ambiguous task resolution.

6. **Current code is the baseline**  
   Upgrade by wrapping and extending current services. Do not discard working ingestion, retrieval, or ontology slices.

7. **Stable contracts before technology swaps**  
   Storage, parser, retrieval, and tool boundaries must stabilize before changing vendors or frameworks.

8. **Provenance is mandatory**  
   Every extracted, promoted, reviewed, or published artifact must carry source and execution provenance.

---

## 4. System Architecture Overview

```text
[Entrypoints]
  |- Chat API
  |- Document API
  |- Ontology Review API
  |- Graph Publish API
  |- MCP API
  |- Admin / Scheduled Jobs
          |
          v
[Task Interpreter]
          |
          v
[Ontology Grounding Layer]
  |- domain hints
  |- entity/type hints
  |- review rules
  |- evidence normalization rules
          |
          v
[Workflow Selector]
  |- deterministic workflow
  |- dynamic agentic flow
          |
          v
[Tool Runtime]
  |- tool registry
  |- policy checks
  |- execution envelopes
  |- trace / audit hooks
          |
   |------------|-------------|--------------|-------------|-------------|
   v            v             v              v             v
[Docs]     [Retrieval]   [Ontology]      [Graph]       [MCP/Web]
   |            |             |              |             |
   v            v             v              v             v
[Postgres] [Postgres/Qdrant] [Postgres] [Neo4j] [External tools/providers]
   |
   v
[Artifacts / Blobs / Cache / Queue]
  |- Postgres blobs now
  |- MinIO later
  |- Redis cache/queue
```

Architectural center:

- **task interpretation**
- **workflow selection**
- **tool runtime**
- **ontology grounding**

Not architectural center:

- chat UI
- answer text generation
- raw query rewriting

---

## 5. System Operating Model

The runtime is built around three primitives.

### Tools

Tools are the atomic execution capabilities of the platform.

Examples:

- parse a document
- retrieve internal chunks
- extract web evidence
- build ontology candidates
- publish graph snapshot
- invoke MCP tool
- generate export artifact

Tools must be:

- typed
- policy-aware
- traceable
- independently testable

### Workflows

Workflows are first-class execution plans that orchestrate tools to resolve a task.

Examples:

- document ingestion workflow
- retrieval workflow
- ontology build workflow
- review and publish workflow
- evidence promotion workflow
- artifact generation workflow

Workflows must define:

- trigger conditions
- input contract
- output contract
- tool sequence or tool graph
- policy and confirmation gates

### Ontology

Ontology is the semantic coordination layer of the runtime.

Ontology provides:

- task grounding
- domain typing
- entity and relation constraints
- workflow hints
- tool affinity hints
- evidence normalization hints
- review and publish boundaries

Ontology is therefore both:

- a persistent knowledge layer, and
- a runtime control layer

---

## 6. Backend Modules

### `task_runtime`
- Task interpretation
- task classification
- runtime state
- final task output assembly

### `workflow_runtime`
- Workflow registry
- deterministic workflow execution
- dynamic workflow orchestration
- workflow versioning

### `tool_registry_service`
- Tool registration
- capability metadata
- risk metadata
- schema lookup
- execution policy lookup

### `tool_runtime`
- Tool input envelope
- validation
- invocation
- retries and timeouts
- trace capture

### `ontology_runtime`
- Ontology grounding
- schema hints
- synonym and taxonomy assets
- semantic normalization rules

### `document_pipeline_service`
- Upload
- parse
- chunk
- embed
- index
- reprocess

### `retrieval_service`
- Internal evidence retrieval
- citation composition
- evidence ranking
- optional query transformation operators

### `web_extract_service`
- Search-based web extract
- URL-specific extract
- temporary evidence capture
- promotion handoff

### `ontology_service`
- Build candidates
- review queue
- versioned publish flow
- graph projection

### `graph_service`
- Graph reads
- graph writes
- graph sync
- provenance links

### `artifact_service`
- Task reports
- exports
- dashboards
- explorer payload generation

Short-term artifact scope:

- `dashboard_payload`: structured JSON assembled from approved evidence, ontology state, graph summaries, and task trace
- `html_report`: server-rendered HTML template report generated from a named template and typed artifact payload
- `export_bundle`: optional package containing report HTML, citations, provenance manifest, and related derived files

Artifact rules:

- dashboards and reports should be generated from approved evidence or policy-allowed evidence bundles, not from arbitrary raw model output
- HTML report templates must be versioned assets with typed input contracts
- PDF export may be added later as a downstream render/export step, not as the initial artifact contract

### `mcp_gateway`
- Tool discovery
- schema cache
- invocation adapter
- permission enforcement

### `chat_entrypoint_service`
- Conversation handling
- runtime selection
- streaming transport

This module is an entry adapter, not the system core.

---

## 7. Agent Orchestration Model

### Deterministic Workflow

Use deterministic workflow when:

- step order is known,
- side effects are controlled,
- outputs are typed and reviewable,
- retries and replays matter.

Examples:

- document ingestion
- ontology build
- review and publish
- evidence promotion
- artifact export

Characteristics:

- explicit step graph
- idempotent job semantics where possible
- durable job state
- audit and replay support

### Dynamic Agentic Flow

Use dynamic agentic flow when:

- task intent is ambiguous,
- the best workflow is not known up front,
- multiple tools must be compared or composed,
- sufficiency or conflict checks determine next actions.

Examples:

- resolving a user task from chat
- deciding whether internal evidence is enough
- deciding whether to escalate from retrieval to web or MCP
- deciding whether output should be an answer, review task, or graph update request

Characteristics:

- runtime branching
- tool and workflow selection at execution time
- intermediate sufficiency checks
- conflict-aware evidence merge

### Standard Task Resolution Workflow

1. Task interpretation
2. Ontology grounding
3. Workflow selection
4. Tool plan construction
5. Tool execution
6. Sufficiency and conflict checks
7. Output assembly
8. Trace, audit, and optional persist or publish

Possible outputs:

- answer
- ontology candidates
- review task
- graph update request
- promoted evidence
- artifact generation

Answer generation is therefore only one possible terminal output.

---

## 8. Tool-Centric Execution Model

Tools are first-class execution primitives. A task is not resolved by sending a raw question to a generic agent loop. It is resolved by selecting and executing tools through policy and workflow.

Tool selection must pass through this chain:

1. **task interpretation**
2. **ontology grounding**
3. **workflow policy**
4. **tool capability metadata**
5. **sufficiency and conflict checks**

This means:

- tool choice is not driven by the raw question alone
- query rewrite is not a central architectural step
- query transformation is only an optional retrieval operator
- retrieval is only one tool family inside a larger runtime

Execution rule:

- tasks select workflows,
- workflows select tools,
- ontology guides both,
- evidence normalizes all outputs before downstream use

---

## 9. Tool Calling & Execution Contract

All tools, internal or external, must conform to one execution contract.

### Tool Registry Model

```json
{
  "tool_name": "string",
  "tool_family": "document | retrieval | ontology | graph | web | mcp | artifact | admin",
  "tool_type": "internal_service | external_adapter | worker_job",
  "version": "string",
  "description": "string",
  "input_schema_ref": "string",
  "output_schema_ref": "string",
  "capabilities": [],
  "risk_level": "low | medium | high",
  "side_effect_level": "read_only | write_internal | write_external",
  "supports_parallel": true,
  "supports_streaming": false,
  "requires_confirmation": false,
  "timeout_ms": 15000,
  "workspace_scope": "workspace | global"
}
```

### Standard Tool Input Schema

```json
{
  "call_id": "string",
  "tool_name": "string",
  "workspace_id": "string",
  "task_id": "string",
  "workflow_id": "string|null",
  "task_type": "string",
  "task_payload": {},
  "ontology_context": {
    "domain": "string|null",
    "entity_hints": [],
    "relation_hints": [],
    "normalization_rules": []
  },
  "arguments": {},
  "constraints": {
    "web_enabled": false,
    "freshness_required": false,
    "max_results": 10,
    "timeout_ms": 15000
  }
}
```

### Standard Tool Output Schema

```json
{
  "call_id": "string",
  "tool_name": "string",
  "status": "success | partial | failed",
  "error_code": "string|null",
  "error_message": "string|null",
  "latency_ms": 0,
  "started_at": "datetime",
  "finished_at": "datetime",
  "evidence": [],
  "artifacts": [],
  "state_patch": {},
  "next_action_hints": [],
  "meta": {
    "provider": "string|null",
    "provider_version": "string|null",
    "trace_id": "string|null"
  }
}
```

### Unified Evidence Contract

```json
{
  "evidence_id": "string",
  "source_type": "internal_chunk | web_page | graph_node | graph_edge | mcp_result | generated_artifact",
  "title": "string",
  "content": "string",
  "summary": "string|null",
  "uri": "string|null",
  "document_id": "string|null",
  "chunk_id": "string|null",
  "page": "integer|null",
  "section": "string|null",
  "sheet_name": "string|null",
  "row_range": "string|null",
  "entity_ids": [],
  "relation_ids": [],
  "score": 0.0,
  "trust_score": 0.0,
  "freshness_ts": "datetime|null",
  "citation_anchor": {
    "anchor_type": "page | section | sheet_row | url_fragment | graph_ref | artifact_ref",
    "label": "string",
    "locator": "string"
  },
  "provenance": {
    "workspace_id": "string",
    "source_id": "string|null",
    "tool_call_id": "string|null",
    "parser_version": "string|null",
    "extractor_version": "string|null",
    "model": "string|null",
    "captured_at": "datetime"
  }
}
```

### Tool Calling Lifecycle

1. Interpret task
2. Ground task with ontology
3. Select workflow
4. Select candidate tools
5. Validate policy and confirmation
6. Execute tool call
7. Normalize evidence and artifacts
8. Run sufficiency and conflict checks
9. Continue workflow, fallback, or finish task

### Tool Routing Policy

Tool routing must be based on:

- task interpretation
- ontology grounding
- workflow policy
- tool capability metadata
- sufficiency checks
- conflict checks

Not just:

- raw question text

### Parallel vs Sequential Calls

Use **parallel** calls when:

- tools are read-only
- inputs are independent
- evidence can be merged later

Use **sequential** calls when:

- later steps depend on earlier outputs
- review or confirmation is required
- sufficiency gates control fallback
- writes must be ordered

### Confirmation & Risk Policy

- `low`: read-only retrieval, graph reads, internal analysis, web extraction
- `medium`: evidence promotion, internal write jobs, ontology auto-approve under policy
- `high`: external writes, destructive admin actions, graph publish outside approved workflow

Rules:

- high-risk actions require explicit confirmation
- medium-risk actions require workspace policy approval
- all writes require audit records

---

## 10. Workflow Selection Policy

Workflow selection is a first-class runtime decision.

Selection inputs:

- entrypoint type
- task type
- ontology-grounded domain
- available tool families
- data sensitivity
- freshness need
- current evidence sufficiency
- detected evidence conflicts

Choose **deterministic workflow** when:

- the task maps to a known backend process
- output shape is predefined
- side effects need explicit control

Examples:

- `document_ingestion`
- `ontology_build`
- `review_publish`
- `promote_evidence`
- `generate_artifact`

Choose **dynamic agentic flow** when:

- the requested outcome is underspecified
- multiple candidate workflows exist
- routing depends on runtime evidence

Examples:

- a chat-triggered task that may end as answer, review task, or evidence promotion
- a task that may need retrieval, web extract, graph lookup, and MCP fallback

Workflow policy must be able to redirect a task from one output class to another if evidence or ontology rules require it.

---

## 11. Retrieval Modes & Retrieval Policy

Retrieval is one tool family within task resolution. It is not the system center.

### Internal RAG Mode

Use when:

- the task targets internal documents
- compliance requires internal-only sources
- citations must point to uploaded workspace documents

Execution:

1. task interpretation
2. internal retrieval
3. sufficiency check
4. synthesize or hand off to next workflow step

### Live Web Extract Mode

Use when:

- web mode is enabled
- the task needs fresh or external information
- immediate response matters more than prior indexing

Execution:

1. task interpretation
2. web extract
3. evidence normalization
4. sufficiency check
5. synthesize or continue workflow

Rules:

- Live Web Extract is immediate answer-time extraction
- it does not require prior indexing into RAG
- save or index after the task is optional and policy-driven

### Hybrid Mode

Use when:

- internal evidence exists but is incomplete or stale
- internal policy must be compared with external evidence
- graph context is useful for resolution or conflict checks

Execution:

1. internal retrieval
2. sufficiency check
3. web fallback if enabled and needed
4. graph or ontology enrichment if needed
5. evidence merge
6. synthesize or route to next output type

### Retrieval Policy

- Internal retrieval is the default starting point for internal work.
- Web fallback is conditional, not automatic.
- Graph and ontology are not only additive retrieval layers; they also guide control decisions.
- Query transformation is optional and should be modeled as a retrieval operator, not as the backbone of the architecture.

### Answer-Oriented Retrieval Resolution

When the requested output class is an answer, the answer path is:

1. intent detection
2. internal retrieval
3. sufficiency check
4. web fallback if enabled
5. evidence merge
6. synthesis
7. citations and tool trace

---

## 12. Document Extraction & Parsing Architecture

### Current Baseline

As of the current repository state, document parsing is implemented with:

- A single converter path: `MarkItDown` via `documents/converters/markdown_converter.py`
- All supported source formats are normalized into markdown before any downstream branch

Current ingestion jobs are:

- `convert_markdown`
- `store_artifacts`
- `build_chunks` (retrieval/both mode only)
- `index_chunks` (retrieval/both mode only)
The system supports three per-document modes:

- `ontology`: convert to markdown and keep ontology pipeline independent from vector indexing
- `retrieval`: convert to markdown + chunk + embed into `document_chunks`
- `both`: run ontology-ready markdown and retrieval indexing in parallel

### Parser Strategy

Short-term strategy:

- keep one converter contract (`MarkdownConverterService`) to normalize file types
- keep chunking as a separate concern in `MarkdownChunker`
- keep ontology and retrieval branches isolated after markdown is produced

### Parser Fallback

Fallback rules:

- use MarkItDown as the default converter
- if markdown is empty, raise `DocumentProcessingError` with a user-facing reason
- for ontology build, read markdown artifact directly (not `document_chunks`)
- keep converter metadata/version in normalized artifact payload

### Parse Output Contract

```json
{
  "document_id": "string",
  "workspace_id": "string",
  "source_object_ref": "string",
  "file_type": "supported by MarkItDown",
  "converter_name": "markitdown",
  "converter_version": "string",
  "ingestion_mode": "ontology | retrieval | both",
  "ocr_used": false,
  "quality_flags": [],
  "markdown_artifact": "document.md",
  "chunks": "present only for retrieval/both",
  "metadata": {
    "filename": "string",
    "mime_type": "string"
  }
}
```

### Chunking Policy by File Type

**PDF**
- chunk by page plus detected structural block
- preserve page anchors
- avoid blind character splitting

**DOCX**
- chunk by heading hierarchy and paragraph groups
- preserve heading path
- keep tables as separate structural chunks

**XLSX**
- create schema chunks for sheet structure
- create row-group chunks for data regions
- preserve sheet name and row range

### Citation Anchor Model

```json
{
  "anchor_type": "page | section | sheet_row",
  "label": "string",
  "locator": "string"
}
```

### Parser Versioning / OCR Fallback / Quality Flags

Required metadata:

- parser name
- parser version
- OCR used or not
- quality flags
- parsed timestamp

Example quality flags:

- `low_text_density`
- `layout_uncertain`
- `ocr_required`
- `table_structure_uncertain`
- `partial_parse`

---

## 13. Ontology & Graph Pipeline

### Ontology Role

Ontology is not only graph output and not only a query expansion layer.

Ontology is the runtime semantic layer used for:

- task grounding
- schema guidance
- tool and workflow hints
- evidence normalization rules
- entity resolution
- review and publish policy
- graph publication

### Ontology Build Pipeline

1. collect source chunks or approved evidence
2. classify domain
3. generate schema hints
4. extract entities
5. extract relations
6. canonicalize and resolve
7. score confidence
8. create review queue
9. publish approved version
10. sync graph projection
11. update runtime semantic assets

### Schema Generation Contract

```json
{
  "schema_id": "string",
  "workspace_id": "string",
  "domain": "string",
  "entity_types": [],
  "relation_types": [],
  "synonym_sets": [],
  "taxonomy_edges": [],
  "version": "string",
  "generated_from": []
}
```

### Entity Resolution Strategy

Resolution should combine:

- exact resolution key match
- alias and synonym match
- ontology type constraints
- context similarity
- review for ambiguous merges

Possible outcomes:

- `matched_existing`
- `created_new`
- `needs_review`

### Provenance Model

Every candidate, node, and edge must record:

- source document or evidence reference
- source chunk or citation anchor
- extractor type and version
- model and prompt version if LLM-assisted
- review status
- reviewer identity if manually approved
- publish version

### Review / Publish Policy

- low-confidence or ambiguous candidates must enter review
- publish only from approved candidates
- publish creates versioned graph snapshots
- Postgres remains the audit and review source of truth

### Graph Boundary

Neo4j stores:

- published ontology entities
- published ontology relations
- graph retrieval views
- graph-side provenance projection

Neo4j does not replace:

- raw document storage
- review queue state
- document chunk storage

### Integration with Retrieval / Query Expansion

Ontology and graph integrate with runtime in four ways:

- retrieval hints and optional query expansion
- tool and workflow guidance
- evidence normalization and conflict detection
- graph publish and downstream explorer artifacts

---

## 14. Ontology-Guided Tooling

Ontology-guided tooling means ontology influences execution before and after retrieval.

Ontology should guide:

- task classification into a domain or task family
- workflow routing
- tool family preference
- argument grounding for tools
- evidence typing and normalization
- conflict detection between sources
- review escalation when semantic mismatches appear

Examples:

- a task grounded to a policy domain may prefer internal retrieval and review workflows
- a task grounded to a market domain may allow web extract sooner
- an evidence bundle with unresolved entity collisions may produce a review task instead of an answer

This is the key shift:

- ontology is not downstream decoration,
- ontology is upstream runtime control.

---

## 15. MCP/Tool Integration Architecture

MCP is the standardized external tool plane.

Responsibilities:

- register external servers
- discover tools
- cache schemas
- invoke tools through the shared execution contract
- apply confirmation, timeout, retry, and audit rules

Usage rule:

- use MCP when internal tools, retrieval, web, or graph are insufficient
- use MCP when an external system action is required
- return MCP output through the same normalized evidence and artifact contracts

Rollout policy:

- read-only first
- write actions later with confirmation gates

---

## 16. Storage & Data Boundaries

### PostgreSQL

Current role:

- primary durable system of record

Current contents:

- workspaces
- conversations and messages
- model and profile config
- documents and document jobs
- document chunks and embeddings
- ontology builds, candidates, versions, and review state
- audit-friendly metadata
- binary document content today

Classification:

- **source of truth:** yes
- **derived data:** some
- **ephemeral data:** no

### MinIO

Current role:

- provisioned in infrastructure but not yet the active primary blob backend

Upgrade role:

- durable object store for uploaded binaries and generated artifacts

Classification:

- **source of truth:** yes for object payloads after adoption
- **derived data:** exported artifacts
- **ephemeral data:** no

### Qdrant

Current role:

- provisioned in infrastructure but not yet the active retrieval backend

Upgrade role:

- derived retrieval index for dense or hybrid search

Classification:

- **source of truth:** no
- **derived data:** yes
- **ephemeral data:** no, rebuildable

### Neo4j

Current role:

- optional published graph projection and graph read backend

Classification:

- **source of truth:** no
- **derived data:** yes
- **ephemeral data:** no, rebuildable from approved versions

### Redis

Role:

- queue, cache, locks, short-lived runtime state

Classification:

- **source of truth:** no
- **derived data:** no
- **ephemeral data:** yes

### Boundary Rules

- Postgres is the current authoritative metadata and review store.
- MinIO and Qdrant are upgrade targets behind ports, not immediate mandatory migrations.
- Neo4j is a derived graph projection.
- Redis must not hold required durable business state.
- Web evidence is ephemeral by default until promoted.

---

## 17. API Boundary Summary

Current stable API families:

### Entry adapters
- `POST /api/v1/chat/messages`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations`

### Document and retrieval
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/jobs`
- `POST /api/v1/documents/{id}/reprocess`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/retrieval/reindex`

### Ontology and graph
- `POST /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds/{id}`
- `GET /api/v1/ontology/builds/{id}/entities`
- `GET /api/v1/ontology/builds/{id}/relations`
- `POST /api/v1/ontology/entities/{id}/review`
- `POST /api/v1/ontology/relations/{id}/review`
- `POST /api/v1/ontology/builds/{id}/publish`
- `GET /api/v1/ontology/graph`

### Tools (shipped in PR-3)
- `GET /api/v1/tools` — lists registered `ToolSpec` records; supports `?family=`
  and `?max_risk=` filters.
- `POST /api/v1/tools/{tool_name}/invoke` — admin execution with the §9
  Standard Tool Input / Output envelopes. `ToolRuntime` handles timeout,
  latency, trace id, and exception wrapping.

Upgrade API boundaries still to add:

- `POST /api/v1/tasks/resolve`
- `GET /api/v1/workflows`
- `POST /api/v1/workflows/{id}/run`
- `POST /api/v1/evidence/promotions`
- `POST /api/v1/artifacts/generate`
- `POST /api/v1/web/extract`
- `POST /api/v1/mcp/invoke`

API rule:

- entrypoint APIs submit tasks
- workflow and tool APIs expose backend control planes
- answer generation should remain one output type, not the only API contract

---

## 18. Phase Roadmap

### Phase 0: Foundation

- stabilize current FastAPI, Postgres, Redis, Celery, and Neo4j baseline
- formalize ports and contracts already visible in code
- keep current DB-backed storage and retrieval working

### Phase 1: Chat + Model Layer

- keep chat as an entry adapter
- harden model routing and runtime selection
- do not let chat define the full architecture

### Phase 2: Parsing + RAG

- formalize parser contract around the documents parser registry
- prefer `marker` for PDF, keep `pypdf` fallback for fast mode, and extend ingestion to `csv`
- improve chunk and citation quality
- keep current Postgres retrieval path while preparing Qdrant as a later backend

### Phase 3: Tool Calling + Retrieval Policy — **in progress (2026-04-20)**

Shipped:

- tool registry (`ToolRegistry` + `ToolSpec`) and tool runtime
  (`ToolRuntime.invoke` with timeout, trace, latency, exception wrapping)
- native function-calling adapters for Anthropic and OpenAI, plus unified
  `LLMMessage` / `LLMToolCall` / `LLMResponse` envelope
- §9 `ToolEnvelope`, `ToolResult`, `Evidence`, `CitationAnchor`, `Provenance`
  contracts in full shape
- first two tools wired: `retrieval.internal`, `ontology.lookup`
- admin endpoints: `GET /api/v1/tools`, `POST /api/v1/tools/{name}/invoke`

Still to land in this phase:

- workflow selection policy + in-code workflow registry
- hybrid retrieval mode (internal + web fallback)
- `/api/v1/tasks/resolve` endpoint and agentic loop routing chat through it
- sufficiency / conflict checks (§9 steps 7-8)

### Phase 4: Ontology + Graph

- upgrade ontology from extraction pipeline to runtime semantic control layer
- add schema hints, semantic routing, and ontology-guided review behavior
- keep versioned publish and Neo4j projection

### Phase 5: MCP + Advanced Agentic

- add MCP tool plane
- support richer dynamic agentic flow
- keep deterministic backend workflows as the default for bounded jobs

### Phase 6: Narrative / Dashboard / Explorer

- generate artifacts from approved evidence and graph state
- add versioned dashboard payloads and HTML report templates behind `artifact_service`
- expose explorer-style backend payloads
- support analyst and admin workflows beyond chat

### Phase 7: Hardening / K8s

- full RBAC and audit
- backup and restore
- observability and SLOs
- performance hardening
- Kubernetes deployment

---

## 19. Risks / Non-Goals

### Key Risks

- drifting back into a generic chat-agent architecture
- over-rotating on answer generation and under-specifying workflows
- treating ontology as only a graph export or query expansion add-on
- forcing technology migrations before contracts are stable
- conflating current placeholder naming with deployed backends

### Non-Goals

- making query rewrite the architectural backbone
- describing graph as only additive retrieval
- treating chat as the system core
- forcing immediate migration to MinIO, Qdrant, or a new orchestration framework
- putting UI or wireframe detail in this document

### Follow-On Documents

- backend API spec
- workflow registry spec
- tool schema spec
- evidence and promotion spec
- ontology review and publish spec
- storage migration spec for MinIO and Qdrant

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Semantic-Reasoning-Agent** (8182 symbols, 19473 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Semantic-Reasoning-Agent/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Semantic-Reasoning-Agent/clusters` | All functional areas |
| `gitnexus://repo/Semantic-Reasoning-Agent/processes` | All execution flows |
| `gitnexus://repo/Semantic-Reasoning-Agent/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
