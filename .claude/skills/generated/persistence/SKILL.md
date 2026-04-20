---
name: persistence
description: "Skill for the Persistence area of Semantic-Reasoning-Agent. 10 symbols across 3 files."
---

# Persistence

10 symbols | 3 files | Cohesion: 90%

## When to Use

- Working with code in `apps/`
- Understanding how main, create_schema, drop_schema work
- Modifying persistence-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | DatabaseManager, create_schema, drop_schema, reset_schema, get_database_manager (+2) |
| `apps/backend/src/semantic_reasoning_agent/services/alembic_service.py` | AlembicService, upgrade |
| `apps/backend/run_migrations.py` | main |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `apps/backend/run_migrations.py:4`
- **`create_schema`** (Function) — `apps/backend/src/semantic_reasoning_agent/persistence/database.py:47`
- **`drop_schema`** (Function) — `apps/backend/src/semantic_reasoning_agent/persistence/database.py:50`
- **`reset_schema`** (Function) — `apps/backend/src/semantic_reasoning_agent/persistence/database.py:53`
- **`get_database_manager`** (Function) — `apps/backend/src/semantic_reasoning_agent/persistence/database.py:59`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DatabaseManager` | Class | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 13 |
| `AlembicService` | Class | `apps/backend/src/semantic_reasoning_agent/services/alembic_service.py` | 11 |
| `main` | Function | `apps/backend/run_migrations.py` | 4 |
| `create_schema` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 47 |
| `drop_schema` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 50 |
| `reset_schema` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 53 |
| `get_database_manager` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 59 |
| `upgrade` | Function | `apps/backend/src/semantic_reasoning_agent/services/alembic_service.py` | 19 |
| `__init__` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 14 |
| `_build_engine` | Function | `apps/backend/src/semantic_reasoning_agent/persistence/database.py` | 24 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Get_conversation_service → Settings` | cross_community | 5 |
| `Get_agent_profile_service → Settings` | cross_community | 5 |
| `Get_model_config_service → Settings` | cross_community | 5 |
| `Get_document_service → Settings` | cross_community | 5 |
| `Get_ontology_service → Settings` | cross_community | 5 |
| `Get_retrieval_service → Settings` | cross_community | 5 |
| `Get_chat_stream_service → Settings` | cross_community | 5 |
| `Get_provider_models_service → Settings` | cross_community | 5 |
| `Get_tool_registry → Settings` | cross_community | 5 |
| `Get_tool_runtime → Settings` | cross_community | 5 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 1 calls |

## How to Explore

1. `gitnexus_context({name: "main"})` — see callers and callees
2. `gitnexus_query({query: "persistence"})` — find related execution flows
3. Read key files listed above for implementation details
