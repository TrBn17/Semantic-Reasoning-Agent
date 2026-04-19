# Backend Architecture

## Scope

This document describes the **current as-is backend architecture** of `apps/backend/src/semantic_reasoning_agent`.

It focuses on:

- current source code structure
- what each package and key file is responsible for
- current request and job flows
- what is already active in runtime
- what has been introduced as a future seam but is not fully wired yet

This is not a target-state architecture. It is a read of the codebase as it exists now.

---

## 1. Current Architecture Summary

The backend is currently a **layered modular monolith** built around:

- **FastAPI** for HTTP entrypoints
- **SQLAlchemy + PostgreSQL** for durable app state
- **Celery + Redis** for async jobs
- **Service layer orchestration** as the main execution model
- **Optional Neo4j projection** for published ontology graph

At the moment, the real runtime center is:

1. `entrypoints` receive HTTP requests
2. `core.container` wires services and adapters
3. `services` execute business logic
4. `persistence.models` store durable state
5. `workers` run async ingestion and ontology jobs

Important architectural fact:

- the codebase has already started introducing **ports**, **repositories**, **domain contracts**, and **tool abstractions**
- but the main runtime still executes mostly through **services calling SQLAlchemy sessions directly**

So the current backend is best described as:

- **service-centric execution**
- **thin HTTP adapters**
- **ORM-backed persistence**
- **adapter seams for future evolution**

---

## 2. High-Level Runtime Topology

```text
FastAPI app
  -> entrypoints/router.py
  -> entrypoints/v1/*.py
  -> entrypoints/dependencies.py
  -> core/container.py
  -> services/*
  -> persistence/database.py + persistence/models/*
  -> infrastructure/*
  -> workers/* for async jobs

External systems currently in play:
  - Postgres: primary durable store
  - Redis: Celery broker/result backend
  - Neo4j: optional ontology graph projection

Provisioned but not yet primary runtime backends:
  - MinIO
  - Qdrant
```

---

## 3. Package Structure

Source root:

```text
apps/backend/src/semantic_reasoning_agent/
  core/
  domain/
  entrypoints/
  infrastructure/
  persistence/
  ports/
  schemas/
  services/
  tools/
  workers/
  main.py
```

### Architectural reading of the folders

- `main.py`: FastAPI bootstrap and app lifecycle
- `core/`: config and dependency composition root
- `entrypoints/`: HTTP adapters and dependency providers
- `services/`: current business orchestration layer
- `persistence/`: database manager, ORM models, early repository layer
- `infrastructure/`: concrete adapters for parser, vector, graph, blob storage, and LLM
- `ports/`: interface contracts for swappable adapters
- `schemas/`: Pydantic request and response models for API boundaries
- `domain/`: domain objects and forward-looking shared contracts
- `tools/`: forward-looking tool abstraction layer
- `workers/`: Celery app, task dispatcher, and background tasks

---

## 4. Core Bootstrap and Composition

### `main.py`

Responsibilities:

- creates the FastAPI app
- installs CORS middleware
- mounts API router under `settings.api_v1_prefix`
- exposes `/health`
- runs startup lifecycle

Important runtime behavior:

- on startup it calls `DatabaseManager.create_schema()`
- then runs Alembic migrations through `AlembicService.upgrade()`

This means schema creation and migration are both part of app startup.

### `core/config.py`

Responsibilities:

- central environment configuration using `pydantic-settings`
- exposes cached `get_settings()`

Defines:

- app settings
- DB settings
- Celery settings
- Neo4j settings
- default workspace and user values
- model/provider env values
- MinIO and Qdrant config placeholders

Important note:

- several config fields already exist for future backends like MinIO and Qdrant
- their presence in config does not mean they are already the active runtime path

### `core/container.py`

Responsibilities:

- composition root for the whole backend
- creates the app-wide singleton `AppContainer`
- wires concrete services and adapters together

Current wiring highlights:

- database manager from `persistence.database`
- adapter registry from `infrastructure.llm.registry`
- graph store from `infrastructure.graph`
- retrieval service
- conversation service
- document service
- ontology service
- chat stream service

Important architectural observation:

- this is the real dependency injection point of the backend
- most runtime behavior depends on how this file wires concrete implementations

Notable current wiring choices:

- chat runtime uses `AdapterRegistry`, but only the `echo` adapter is currently registered
- ontology extraction uses `OpenDomainLLMExtractor`, which calls Anthropic directly
- `OntologyRepository` is used only to power `OntologySchemaRegistry`

---

## 5. HTTP Layer

### `entrypoints/router.py`

Registers all API groups:

- `agents`
- `agent_profiles`
- `auth`
- `chat`
- `conversations`
- `documents`
- `models`
- `ontology`
- `retrieval`

### `entrypoints/dependencies.py`

Thin dependency-provider module that exposes services from `core.container`.

This keeps route handlers thin and avoids manual object construction inside route files.

### `entrypoints/v1/*.py`

These files are thin FastAPI adapters.

They typically do three things:

1. validate request via Pydantic schema
2. call one service method
3. map domain/service exceptions to HTTP errors

#### `entrypoints/v1/auth.py`

- returns a synthetic `GET /me`
- current auth is placeholder and driven from default settings

#### `entrypoints/v1/chat.py`

- exposes `POST /chat/messages`
- delegates to `ChatStreamService.send_message`

#### `entrypoints/v1/conversations.py`

- create conversation
- list conversations
- get one conversation
- change runtime model selection
- change attached agent profile

#### `entrypoints/v1/documents.py`

- upload document
- list documents
- get document
- get document jobs
- reprocess document

#### `entrypoints/v1/retrieval.py`

- search indexed chunks
- trigger reindexing via document reprocess

#### `entrypoints/v1/ontology.py`

- create ontology build
- inspect build state
- list entity and relation candidates
- review candidates
- publish build
- read current graph

#### `entrypoints/v1/models.py`

- returns the model catalog

#### `entrypoints/v1/agents.py`

- returns task catalog and model/provider settings
- updates workspace-level agent settings

#### `entrypoints/v1/agent_profiles.py`

- CRUD-like operations for agent profiles
- set default profile per workspace

---

## 6. Service Layer

The `services/` package is the current business core.

This is the most important package in the current codebase.

### `services/conversation_service.py`

Responsibilities:

- create and fetch conversations
- persist chat messages
- switch runtime provider/model
- attach or change agent profile
- resolve effective system prompt

Characteristics:

- directly uses SQLAlchemy sessions
- directly manipulates `ConversationORM`, `MessageORM`, and `AgentProfileORM`
- coordinates with `ModelConfigService` and `AgentProfileService`

### `services/chat_stream_service.py`

Responsibilities:

- execute chat send-message flow
- validate selected provider/model readiness
- append user and assistant messages
- optionally run retrieval grounding

Current behavior:

- gets adapter from `AdapterRegistry`
- generates assistant text via `adapter.generate_reply(...)`
- if `use_retrieval=true`, it performs retrieval and replaces the reply with a citation-grounded synthetic response

Important limitation:

- despite the name `ChatStreamService`, current implementation is not true streaming orchestration yet
- it returns one assembled response object

### `services/document_service.py`

Responsibilities:

- upload documents
- register ingestion jobs
- reprocess documents
- execute ingestion pipeline in workers

Current ingestion pipeline steps:

1. `parse_document`
2. `build_chunks`
3. `embed_chunks`
4. `upsert_qdrant`

Important implementation note:

- the last step is named `upsert_qdrant`
- but current chunk storage is still Postgres-backed through `DocumentChunkORM`
- so the step name is forward-looking, not proof of an active Qdrant backend

### `services/retrieval_service.py`

Responsibilities:

- convert parsed documents into indexed chunks
- write indexed chunks to storage
- remove chunks for a document
- search chunk data
- compose citations

Current retrieval architecture:

- chunk embeddings are generated by `TokenVectorBackend`
- embeddings are stored as JSON in Postgres
- similarity search is done in Python over rows loaded from Postgres

So current retrieval is:

- not Qdrant-backed
- not dense-vector-provider-backed
- not reranker-based
- but a local DB-backed lexical/token-vector implementation

### `services/ontology_service.py`

Responsibilities:

- create ontology builds
- queue ontology processing
- execute ontology extraction flow
- persist candidate entities and relations
- expose review workflow
- publish approved graph versions
- read graph state

Current ontology pipeline shape:

1. validate indexed document exists
2. queue build
3. classify domain
4. extract entities
5. extract relations
6. resolve entities
7. build graph upsert plan
8. verify Neo4j path
9. mark build completed
10. later publish approved snapshot

Important architectural fact:

- ontology is already a real backend subsystem, not just a placeholder
- Postgres stores the authoritative review and version state
- Neo4j is a projection target for published versions

### `services/model_config_service.py`

Responsibilities:

- manage provider configuration per workspace
- manage task-to-model assignments
- expose model catalog
- resolve runtime provider/model for task types
- check model readiness

Important nuance:

- the service knows about `openai`, `anthropic`, `gemini`, `ollama`, and `echo`
- but the runtime adapter registry currently only wires `echo`
- so the config/catalog layer is ahead of the runtime adapter implementation

### `services/agent_profile_service.py`

Responsibilities:

- CRUD-like operations for agent profiles
- manage per-profile task-model assignments
- manage default profile per workspace

### `services/secret_service.py`

Responsibilities:

- store provider secrets in database
- retrieve and mask secrets
- act as a small abstraction over secret persistence

Current implementation:

- uses `ProviderSecretORM`
- secrets are stored in Postgres

### `services/alembic_service.py`

Responsibilities:

- run Alembic migrations against the configured DB
- bridge runtime startup with migration execution

---

## 7. Persistence Layer

### `persistence/database.py`

Responsibilities:

- create SQLAlchemy engine
- expose session context manager
- create/drop/reset schema
- cache the `DatabaseManager`

This is the low-level DB runtime entrypoint.

### `persistence/models/base.py`

Responsibilities:

- declarative SQLAlchemy base
- shared UTC timestamp helper

### `persistence/models/conversations.py`

Tables:

- `conversations`
- `messages`

Supports:

- stored chat history
- runtime model selection per conversation

### `persistence/models/agent_profiles.py`

Tables for:

- agent profile definitions
- per-profile task-model assignments

### `persistence/models/providers.py`

Tables for:

- provider config per workspace
- task-model config per workspace
- provider secrets

### `persistence/models/documents.py`

Tables for:

- `documents`
- `document_jobs`
- `document_chunks`

Important note:

- raw binary document content is currently stored in `documents.binary_content`
- chunk embeddings are currently stored in `document_chunks.embedding`

### `persistence/models/ontology.py`

Tables for:

- `ontology_builds`
- `ontology_build_steps`
- `ontology_candidate_entities`
- `ontology_candidate_relations`
- `ontology_versions`
- `ontology_entities`
- `ontology_relations`

This is the most mature domain-specific persistence slice in the backend.

### `persistence/repositories/*.py`

Current status:

- repository layer has been introduced
- but only lightly used today

Files:

- `document_repo.py`: basic document reads
- `chunk_repo.py`: basic chunk reads
- `ontology_repo.py`: read helpers used by schema registry

Important architectural observation:

- repositories are not yet the main access path
- most services still use `database_manager.session()` directly

---

## 8. Infrastructure Adapters

The `infrastructure/` package holds concrete implementations behind ports.

### `infrastructure/parsers/local_parser.py`

Current active parser implementation.

Responsibilities:

- parse PDF with `pypdf.PdfReader`
- parse DOCX with `python-docx`
- parse XLSX with `openpyxl`
- emit normalized parsed chunk objects used by ingestion

Current parser behavior:

- PDF: one chunk per extractable page
- DOCX: chunk by heading/paragraph groups, tables separately
- XLSX: schema chunk plus row-group chunks

### `infrastructure/parsers/models.py`

Current active internal parser data model:

- `ParsedChunk`
- `ParsedDocument`
- `IndexedChunk`

This is the data shape actually used by `DocumentService` and `RetrievalService`.

### `infrastructure/vector/token_vector_backend.py`

Current active vector backend.

Responsibilities:

- tokenize text
- build token-frequency maps
- compute cosine similarity

This is a simple local similarity backend, not a production vector DB integration.

### `infrastructure/storage/database_blob_store.py`

Current active object store implementation.

Behavior:

- stores and returns document content directly from DB flow
- acts as a placeholder object store abstraction

Important note:

- config includes MinIO settings
- but runtime storage is still effectively DB-backed

### `infrastructure/graph/__init__.py`

Factory that chooses between:

- `NullGraphStore`
- `Neo4jGraphStore`

based on `NEO4J_ENABLED`.

### `infrastructure/graph/null_graph_store.py`

Fallback no-op implementation for graph operations.

### `infrastructure/graph/neo4j_graph_store.py`

Current concrete Neo4j integration.

Responsibilities:

- verify Neo4j connection
- sync published ontology snapshot
- read latest ontology graph back from Neo4j

Important boundary:

- it only handles published ontology snapshots
- it is not the source of truth for review/build state

### `infrastructure/llm/registry.py`

Current provider registry.

Current runtime adapter coverage:

- only `echo`

This means:

- the system can catalog multiple providers
- but chat runtime only has one implemented adapter path today

### `infrastructure/llm/echo.py`

Simple local adapter used for smoke-test chat flow.

### `infrastructure/ontology/llm_prompts.py`

Prompt builders for ontology extraction.

### `infrastructure/ontology/llm_extractor.py`

Current ontology extraction implementation used by the container:

- `OpenDomainLLMExtractor`

Behavior:

- gets model assignment via `TaskModelResolverPort` (implemented by `ModelConfigService`)
- reads prior entity/relation types from `OntologySchemaRegistry`
- builds prompt
- calls Anthropic SDK directly
- validates JSON output with Pydantic
- emits `ExtractionResult`
- consumes domain-level `OntologySourceChunk` inputs instead of persistence ORM chunk objects

Important architecture nuance:

- ontology LLM extraction bypasses the generic chat adapter registry
- so there are effectively two LLM integration paths today:
  - adapter-registry path for chat
  - direct Anthropic SDK path for ontology extraction

---

## 9. Ports and Interface Boundaries

The `ports/` folder defines interface seams for future swapping.

### Active or meaningful ports

- `llm_adapter.py`: interface for chat runtime adapters
- `vector_backend.py`: interface for embedding/similarity backend
- `object_store.py`: interface for blob storage
- `graph_store.py`: graph projection interface
- `ontology_extractor.py`: ontology extraction contract
- `parser.py`: parser contract
- `task_model_resolver.py`: task-to-model resolution and readiness contract
- `secret_repo.py`: secret repository contract

Architectural reading:

- these ports are real seams
- but only some are fully respected end-to-end today

Current examples:

- `VectorBackendPort` is used by `RetrievalService`
- `ObjectStorePort` is used by `DocumentService`
- `GraphStore` is used by `OntologyService`
- `OntologyExtractorPort` is used by `OntologyService`
- `TaskModelResolverPort` is used by `OpenDomainLLMExtractor`

Recent contract alignment:

- `OntologyExtractorPort` now uses domain `OntologySourceChunk` instead of `DocumentChunkORM`
- `ParserPort` now returns domain contract `ParsedDocument` instead of infrastructure parser models

---

## 10. Domain Layer

The `domain/` package is currently a mix of active ontology domain models and forward-looking shared contracts.

### `domain/ontology/models.py`

Active domain types:

- `ExtractedEntity`
- `ExtractedRelation`
- `ExtractionResult`
- `OntologySourceChunk`

These are used in the ontology extraction and publish flow.

### `domain/ontology/pipeline_steps.py`

Defines canonical ontology pipeline step names used by `OntologyService`.

### `domain/ontology/scoring.py`

Holds ontology scoring helpers.

### `domain/contracts/*`

Forward-looking shared contracts for:

- parsed documents
- ontology context
- evidence
- tool envelopes and tool results

Important current status:

- these contracts are mostly **not yet the main runtime data path**
- they look like the intended future abstraction layer for tool/workflow-centric execution

Concrete example:

- current ingestion uses `infrastructure.parsers.models.ParsedDocument`
- not `domain.contracts.parsed_document.ParsedDocument`

Recent change:

- ontology extraction path now uses domain input contracts end-to-end (`OntologySourceChunk`) between service and extractor port

---

## 11. Tools Layer

### `tools/base.py`

Introduces a generic `Tool` abstraction:

- a tool consumes `ToolEnvelope`
- returns `ToolResult`

### `tools/ontology/schema_registry.py`

This is the only ontology-related tooling piece already wired into runtime.

Responsibilities:

- read previously observed entity and relation types from candidate rows
- expose them as an emergent schema prior for ontology extraction

Important note:

- the general tool runtime does not exist yet
- the tools package is currently a forward seam, not the main execution model

---

## 12. Workers and Async Execution

### `workers/celery_app.py`

Defines the Celery application:

- broker from Redis
- result backend from Redis
- JSON serialization

### `workers/task_dispatcher.py`

Small dispatcher wrapper used by services to enqueue jobs.

Current jobs:

- document processing
- ontology build processing

### `workers/worker_tasks.py`

Actual Celery task entrypoints:

- `process_document_task`
- `process_ontology_build_task`

They resolve the app container and then call service methods.

Architectural reading:

- worker tasks are intentionally thin
- services still own the pipeline logic

---

## 13. Schemas Layer

The `schemas/` folder holds Pydantic request/response DTOs for API boundaries.

Files are grouped by API surface:

- `auth.py`
- `chat.py`
- `documents.py`
- `retrieval.py`
- `ontology.py`
- `agents.py`
- `agent_profiles.py`

Architectural role:

- keep HTTP contracts separate from ORM models
- provide typed boundary models for routes and clients

---

## 14. Current End-to-End Flows

### Chat flow

```text
POST /chat/messages
  -> entrypoints/v1/chat.py
  -> ChatStreamService.send_message()
  -> ConversationService.get_conversation()
  -> ModelConfigService.is_ready()
  -> AdapterRegistry.get()
  -> adapter.generate_reply()
  -> optional RetrievalService.search()
  -> ConversationService.append_message()
```

Current state:

- synchronous
- no real streaming transport
- retrieval grounding is optional and shallow

### Document ingestion flow

```text
POST /documents/upload
  -> DocumentService.upload_document()
  -> persist DocumentORM + DocumentJobORM rows
  -> enqueue Celery job

worker
  -> DocumentService.process_document()
  -> parse_document()
  -> RetrievalService.prepare_document_chunks()
  -> RetrievalService.upsert_chunks()
  -> update document/job state
```

Current state:

- async pipeline is real
- parser stack is local
- chunk storage is Postgres-backed

### Retrieval flow

```text
POST /retrieval/search
  -> RetrievalService.search()
  -> load chunks from Postgres
  -> embed query via TokenVectorBackend
  -> score in Python
  -> return citations
```

Current state:

- simple but functional
- no Qdrant yet
- no reranker yet

### Ontology flow

```text
POST /ontology/builds
  -> OntologyService.create_build()
  -> persist build + steps
  -> enqueue Celery job

worker
  -> OntologyService.process_build()
  -> map persistence chunks to domain `OntologySourceChunk`
  -> OpenDomainLLMExtractor.extract_ontology_candidates()
  -> persist candidate entities/relations
  -> review
  -> publish
  -> optional Neo4j sync
```

Current state:

- this is the richest backend workflow in the codebase
- review and publish are first-class
- Postgres is authoritative
- Neo4j is downstream projection

---

## 15. As-Is Architectural Assessment

### What is already solid

- clear composition root
- thin HTTP layer
- workable service layer
- durable Postgres-backed state
- real async pipelines
- real ontology review/publish lifecycle
- useful ports for future backend swaps

### What is transitional

- repository layer exists but is not the default access path yet
- tool abstraction exists but is not yet the runtime execution model
- domain contracts exist but are only partially wired
- config already anticipates MinIO/Qdrant, but runtime still uses Postgres-backed storage/retrieval

### Current architecture in one sentence

The backend today is a **service-centric FastAPI monolith with Celery jobs, SQLAlchemy persistence, optional Neo4j graph projection, and an in-progress refactor toward ports/repositories/tools-based modularity**.

---

## 16. File Map by Importance

If someone needs to understand the backend quickly, read in this order:

1. `main.py`
2. `core/config.py`
3. `core/container.py`
4. `entrypoints/router.py`
5. `entrypoints/v1/*.py`
6. `services/document_service.py`
7. `services/retrieval_service.py`
8. `services/ontology_service.py`
9. `services/chat_stream_service.py`
10. `persistence/models/*.py`
11. `infrastructure/parsers/local_parser.py`
12. `infrastructure/vector/token_vector_backend.py`
13. `infrastructure/graph/*.py`
14. `workers/*.py`

---

## 17. Key Takeaways

- The actual backend architecture today is **not yet tool-runtime-first**.
- The actual center of execution is still **service layer + ORM + Celery jobs**.
- Ontology is the strongest domain slice already implemented.
- Retrieval and storage still run on local/Postgres-backed implementations, even though config and naming already prepare for MinIO/Qdrant.
- The codebase is actively moving toward a cleaner architecture with ports, repositories, domain contracts, and tools, but that refactor is still partial.
