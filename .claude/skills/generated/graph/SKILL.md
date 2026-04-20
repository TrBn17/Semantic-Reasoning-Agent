---
name: graph
description: "Skill for the Graph area of Semantic-Reasoning-Agent. 24 symbols across 5 files."
---

# Graph

24 symbols | 5 files | Cohesion: 84%

## When to Use

- Working with code in `apps/`
- Understanding how get_graph, get_graph, sync_published_graph work
- Modifying graph-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | get_graph, _label_exists, _deserialize_version, _deserialize_entity, _deserialize_relation (+11) |
| `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | OntologyEntityResponse, OntologyRelationResponse, OntologyGraphResponse |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/null_graph_store.py` | get_graph, NullGraphStore |
| `apps/backend/src/semantic_reasoning_agent/ports/graph_store.py` | GraphStoreError, GraphStore |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/__init__.py` | build_graph_store |

## Entry Points

Start here when exploring this area:

- **`get_graph`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/null_graph_store.py:16`
- **`get_graph`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py:59`
- **`sync_published_graph`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py:44`
- **`verify_connection`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py:37`
- **`delete_workspace`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py:125`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `OntologyEntityResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | 138 |
| `OntologyRelationResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | 151 |
| `OntologyGraphResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | 178 |
| `GraphStoreError` | Class | `apps/backend/src/semantic_reasoning_agent/ports/graph_store.py` | 20 |
| `GraphStore` | Class | `apps/backend/src/semantic_reasoning_agent/ports/graph_store.py` | 24 |
| `NullGraphStore` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/null_graph_store.py` | 6 |
| `Neo4jGraphStore` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 19 |
| `get_graph` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/null_graph_store.py` | 16 |
| `get_graph` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 59 |
| `sync_published_graph` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 44 |
| `verify_connection` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 37 |
| `delete_workspace` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 125 |
| `build_graph_store` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/__init__.py` | 8 |
| `_label_exists` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 135 |
| `_deserialize_version` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 281 |
| `_deserialize_entity` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 292 |
| `_deserialize_relation` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 308 |
| `_deserialize_datetime` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 330 |
| `_deserialize_json_map` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 336 |
| `_serialize_version` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/graph/neo4j_graph_store.py` | 239 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `_execute_answer_workflow → OntologyEntityResponse` | cross_community | 6 |
| `_execute_answer_workflow → OntologyRelationResponse` | cross_community | 6 |
| `Get_knowledge_graph → OntologyEntityResponse` | cross_community | 5 |
| `Get_knowledge_graph → OntologyRelationResponse` | cross_community | 5 |
| `Patch_relation → OntologyEntityResponse` | cross_community | 5 |
| `_execute_answer_workflow → OntologyGraphResponse` | cross_community | 5 |
| `Get_knowledge_graph → OntologyGraphResponse` | cross_community | 4 |
| `Patch_relation → OntologyRelationResponse` | cross_community | 4 |
| `Get_graph → OntologyVersionResponse` | cross_community | 3 |
| `Get_graph → _deserialize_datetime` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 1 calls |

## How to Explore

1. `gitnexus_context({name: "get_graph"})` — see callers and callees
2. `gitnexus_query({query: "graph"})` — find related execution flows
3. Read key files listed above for implementation details
