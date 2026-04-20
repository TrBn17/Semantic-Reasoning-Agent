---
name: services
description: "Skill for the Services area of Semantic-Reasoning-Agent. 363 symbols across 70 files."
---

# Services

363 symbols | 70 files | Cohesion: 75%

## When to Use

- Working with code in `apps/`
- Understanding how test_ontology_source_chunk_construct, enqueue_ontology_build_processing, classify_document_domain work
- Modifying services-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/services/ontology_service.py` | create_build, get_build, approve_all_candidates, extract_sync_and_publish, ingest_documents_sync_publish (+29) |
| `apps/backend/src/semantic_reasoning_agent/services/document_service.py` | reprocess_documents, _list_document_ids, _prepare_reprocess, DocumentService, DocumentNotFoundError (+23) |
| `apps/backend/src/semantic_reasoning_agent/services/model_config_service.py` | ModelConfigService, __init__, list_models, get_catalog, get_agent_settings (+16) |
| `apps/backend/src/semantic_reasoning_agent/services/provider_models_service.py` | ProviderModelsService, __init__, ProviderModel, OpenAIModelsClient, get_models (+13) |
| `apps/backend/src/semantic_reasoning_agent/services/conversation_service.py` | ConversationService, utc_now, ConversationNotFoundError, ConversationPolicyError, list_conversations (+9) |
| `apps/backend/src/semantic_reasoning_agent/entrypoints/dependencies.py` | get_conversation_service, get_agent_profile_service, get_model_config_service, get_document_service, get_ontology_service (+8) |
| `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py` | TaskRuntime, _execute_answer_workflow, _build_ontology_context, _select_tools, _tool_system_prompt (+8) |
| `apps/backend/src/semantic_reasoning_agent/services/agent_profile_service.py` | AgentProfileService, __init__, utc_now, create_profile, set_default_profile (+8) |
| `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py` | RuntimeAuditService, _utc_now, create_task_run, set_task_workflow, complete_task_run (+6) |
| `apps/backend/tests/services/test_tool_runtime.py` | _spec, _envelope, test_unknown_tool_returns_failed_result, test_confirmation_required_blocks_invocation, test_exception_caught_and_wrapped (+6) |

## Entry Points

Start here when exploring this area:

- **`test_ontology_source_chunk_construct`** (Function) — `apps/backend/tests/contracts/test_contracts_smoke.py:162`
- **`enqueue_ontology_build_processing`** (Function) — `apps/backend/src/semantic_reasoning_agent/workers/task_dispatcher.py:6`
- **`classify_document_domain`** (Function) — `apps/backend/src/semantic_reasoning_agent/ports/ontology_extractor.py:8`
- **`extract_ontology_candidates`** (Function) — `apps/backend/src/semantic_reasoning_agent/ports/ontology_extractor.py:11`
- **`session`** (Function) — `apps/backend/src/semantic_reasoning_agent/persistence/database.py:36`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `RetrievalReindexResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/retrieval.py` | 44 |
| `OntologyBuildCreateRequest` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | 37 |
| `KnowledgeGraphIngestResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/ontology.py` | 171 |
| `OntologyBuildNotFoundError` | Class | `apps/backend/src/semantic_reasoning_agent/services/ontology_errors.py` | 9 |
| `OntologyBuildError` | Class | `apps/backend/src/semantic_reasoning_agent/services/ontology_errors.py` | 13 |
| `OntologyBuildORM` | Class | `apps/backend/src/semantic_reasoning_agent/persistence/models/ontology.py` | 9 |
| `OntologyBuildStepORM` | Class | `apps/backend/src/semantic_reasoning_agent/persistence/models/ontology.py` | 45 |
| `OntologySourceChunk` | Class | `apps/backend/src/semantic_reasoning_agent/domain/ontology/models.py` | 40 |
| `TaskDispatcher` | Class | `apps/backend/src/semantic_reasoning_agent/workers/task_dispatcher.py` | 0 |
| `AppContainer` | Class | `apps/backend/src/semantic_reasoning_agent/core/container.py` | 35 |
| `WorkflowSpec` | Class | `apps/backend/src/semantic_reasoning_agent/services/workflow_runtime.py` | 12 |
| `WorkflowRegistry` | Class | `apps/backend/src/semantic_reasoning_agent/services/workflow_runtime.py` | 27 |
| `WorkflowRuntime` | Class | `apps/backend/src/semantic_reasoning_agent/services/workflow_runtime.py` | 38 |
| `TaskRuntime` | Class | `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py` | 46 |
| `DatabaseSecretRepository` | Class | `apps/backend/src/semantic_reasoning_agent/services/secret_service.py` | 15 |
| `SecretService` | Class | `apps/backend/src/semantic_reasoning_agent/services/secret_service.py` | 90 |
| `RuntimeAuditService` | Class | `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py` | 24 |
| `RetrievalService` | Class | `apps/backend/src/semantic_reasoning_agent/services/retrieval_service.py` | 18 |
| `ProviderModelsService` | Class | `apps/backend/src/semantic_reasoning_agent/services/provider_models_service.py` | 197 |
| `OntologyService` | Class | `apps/backend/src/semantic_reasoning_agent/services/ontology_service.py` | 58 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Get_agent_catalog → Get` | cross_community | 7 |
| `Get_agent_catalog → ProviderModel` | cross_community | 7 |
| `Publish_build → OntologyBuildStepResponse` | cross_community | 6 |
| `Run_workflow → OntologyGraphError` | cross_community | 6 |
| `Get_agent_settings → Get` | cross_community | 6 |
| `Get_agent_catalog → OpenAIModelsClient` | cross_community | 6 |
| `Get_agent_catalog → AnthropicModelsClient` | cross_community | 6 |
| `Resolve_task → OntologyGraphError` | cross_community | 6 |
| `List_models → Get` | cross_community | 6 |
| `List_models → ProviderModel` | cross_community | 6 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Contracts | 10 calls |
| Graph | 4 calls |
| Infrastructure | 4 calls |
| Schemas | 2 calls |
| Parsers | 2 calls |
| Persistence | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_ontology_source_chunk_construct"})` — see callers and callees
2. `gitnexus_query({query: "services"})` — find related execution flows
3. Read key files listed above for implementation details
