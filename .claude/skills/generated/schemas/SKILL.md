---
name: schemas
description: "Skill for the Schemas area of Semantic-Reasoning-Agent. 21 symbols across 11 files."
---

# Schemas

21 symbols | 11 files | Cohesion: 86%

## When to Use

- Working with code in `apps/`
- Understanding how upload_documents, upload_documents, list_tool_calls work
- Modifying schemas-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | CitationAnchorSchema, ProvenanceSchema, EvidenceSchema, ToolMetaSchema, StandardToolOutputSchema |
| `apps/backend/src/semantic_reasoning_agent/schemas/agents.py` | ProviderFieldDefinition, ProviderFieldValue, ProviderConfigResponse |
| `apps/backend/src/semantic_reasoning_agent/services/model_config_service.py` | _build_provider_response, _mask_runtime_value |
| `apps/backend/src/semantic_reasoning_agent/schemas/documents.py` | DocumentUploadFailure, DocumentBatchUploadResponse |
| `apps/backend/src/semantic_reasoning_agent/schemas/tasks.py` | ToolCallRecord, WorkflowRunRecord |
| `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py` | list_tool_calls, list_workflow_runs |
| `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py` | _evidence_to_schema |
| `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | _result_to_schema |
| `apps/backend/src/semantic_reasoning_agent/services/document_service.py` | upload_documents |
| `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/documents.py` | upload_documents |

## Entry Points

Start here when exploring this area:

- **`upload_documents`** (Function) — `apps/backend/src/semantic_reasoning_agent/services/document_service.py:137`
- **`upload_documents`** (Function) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/documents.py:46`
- **`list_tool_calls`** (Function) — `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py:255`
- **`list_task_tool_calls`** (Function) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tasks.py:51`
- **`list_workflow_runs`** (Function) — `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py:234`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CitationAnchorSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 99 |
| `ProvenanceSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 107 |
| `EvidenceSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 119 |
| `ToolMetaSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 143 |
| `StandardToolOutputSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 151 |
| `ProviderFieldDefinition` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/agents.py` | 31 |
| `ProviderFieldValue` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/agents.py` | 40 |
| `ProviderConfigResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/agents.py` | 47 |
| `DocumentUploadFailure` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/documents.py` | 54 |
| `DocumentBatchUploadResponse` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/documents.py` | 59 |
| `ToolCallRecord` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tasks.py` | 110 |
| `WorkflowRunRecord` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tasks.py` | 96 |
| `upload_documents` | Function | `apps/backend/src/semantic_reasoning_agent/services/document_service.py` | 137 |
| `upload_documents` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/documents.py` | 46 |
| `list_tool_calls` | Function | `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py` | 255 |
| `list_task_tool_calls` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tasks.py` | 51 |
| `list_workflow_runs` | Function | `apps/backend/src/semantic_reasoning_agent/services/runtime_audit_service.py` | 234 |
| `_evidence_to_schema` | Function | `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py` | 537 |
| `_result_to_schema` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | 122 |
| `_build_provider_response` | Function | `apps/backend/src/semantic_reasoning_agent/services/model_config_service.py` | 548 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Upload_documents → DocumentProcessingError` | cross_community | 4 |
| `Upload_documents → _is_supported_document` | cross_community | 4 |
| `Upload_documents → UnsupportedDocumentTypeError` | cross_community | 4 |
| `Upload_documents → Utc_now` | cross_community | 4 |
| `Invoke_tool → EvidenceSchema` | cross_community | 3 |
| `Invoke_tool → CitationAnchorSchema` | cross_community | 3 |
| `Invoke_tool → ProvenanceSchema` | cross_community | 3 |
| `Invoke_tool → StandardToolOutputSchema` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 4 calls |

## How to Explore

1. `gitnexus_context({name: "upload_documents"})` — see callers and callees
2. `gitnexus_query({query: "schemas"})` — find related execution flows
3. Read key files listed above for implementation details
