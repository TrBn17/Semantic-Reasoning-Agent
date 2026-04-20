---
name: ports
description: "Skill for the Ports area of Semantic-Reasoning-Agent. 6 symbols across 6 files."
---

# Ports

6 symbols | 6 files | Cohesion: 100%

## When to Use

- Working with code in `apps/`
- Understanding how VectorBackendPort, TokenVectorBackend, ObjectStorePort work
- Modifying ports-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/ports/vector_backend.py` | VectorBackendPort |
| `apps/backend/src/semantic_reasoning_agent/services/retrieval_service.py` | __init__ |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/vector/token_vector_backend.py` | TokenVectorBackend |
| `apps/backend/src/semantic_reasoning_agent/ports/object_store.py` | ObjectStorePort |
| `apps/backend/src/semantic_reasoning_agent/services/document_service.py` | __init__ |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/storage/database_blob_store.py` | DatabaseBlobStore |

## Entry Points

Start here when exploring this area:

- **`VectorBackendPort`** (Class) — `apps/backend/src/semantic_reasoning_agent/ports/vector_backend.py:5`
- **`TokenVectorBackend`** (Class) — `apps/backend/src/semantic_reasoning_agent/infrastructure/vector/token_vector_backend.py:10`
- **`ObjectStorePort`** (Class) — `apps/backend/src/semantic_reasoning_agent/ports/object_store.py:5`
- **`DatabaseBlobStore`** (Class) — `apps/backend/src/semantic_reasoning_agent/infrastructure/storage/database_blob_store.py:5`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `VectorBackendPort` | Class | `apps/backend/src/semantic_reasoning_agent/ports/vector_backend.py` | 5 |
| `TokenVectorBackend` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/vector/token_vector_backend.py` | 10 |
| `ObjectStorePort` | Class | `apps/backend/src/semantic_reasoning_agent/ports/object_store.py` | 5 |
| `DatabaseBlobStore` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/storage/database_blob_store.py` | 5 |
| `__init__` | Function | `apps/backend/src/semantic_reasoning_agent/services/retrieval_service.py` | 19 |
| `__init__` | Function | `apps/backend/src/semantic_reasoning_agent/services/document_service.py` | 47 |

## How to Explore

1. `gitnexus_context({name: "VectorBackendPort"})` — see callers and callees
2. `gitnexus_query({query: "ports"})` — find related execution flows
3. Read key files listed above for implementation details
