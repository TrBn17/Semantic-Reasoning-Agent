---
name: contracts
description: "Skill for the Contracts area of Semantic-Reasoning-Agent. 39 symbols across 15 files."
---

# Contracts

39 symbols | 15 files | Cohesion: 79%

## When to Use

- Working with code in `apps/`
- Understanding how run, test_citation_and_evidence_construct, test_tool_envelope_construct work
- Modifying contracts-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/tests/contracts/test_contracts_smoke.py` | test_citation_and_evidence_construct, test_tool_envelope_construct, test_tool_constraints_defaults, test_tool_result_construct, test_tool_meta_default (+2) |
| `apps/backend/src/semantic_reasoning_agent/tools/retrieval/internal_retrieval_tool.py` | _result_to_evidence, _anchor_from_citation, _format_row_range, run |
| `apps/backend/src/semantic_reasoning_agent/tools/ontology/ontology_lookup_tool.py` | _entity_to_evidence, _relation_to_evidence, run, _current_version_result |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py` | ToolConstraints, ToolEnvelope, ToolMeta, ToolResult |
| `apps/backend/src/semantic_reasoning_agent/services/tool_runtime.py` | _normalize_evidence, _utc_now, _failed |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/evidence.py` | CitationAnchor, Provenance, Evidence |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | LLMToolCall, LLMUsage, LLMResponse |
| `apps/backend/src/semantic_reasoning_agent/services/task_runtime.py` | _invoke_llm_tool_call, _invoke_fallback_retrieval |
| `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | invoke_tool, _payload_to_envelope |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/parsed_document.py` | ParsedChunk, ParsedDocument |

## Entry Points

Start here when exploring this area:

- **`run`** (Function) — `apps/backend/tests/services/test_tool_runtime.py:55`
- **`test_citation_and_evidence_construct`** (Function) — `apps/backend/tests/contracts/test_contracts_smoke.py:57`
- **`test_tool_envelope_construct`** (Function) — `apps/backend/tests/contracts/test_contracts_smoke.py:26`
- **`test_tool_constraints_defaults`** (Function) — `apps/backend/tests/contracts/test_contracts_smoke.py:117`
- **`spec`** (Function) — `apps/backend/src/semantic_reasoning_agent/services/tool_registry.py:51`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `CitationAnchor` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/evidence.py` | 27 |
| `Provenance` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/evidence.py` | 41 |
| `Evidence` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/evidence.py` | 54 |
| `ToolConstraints` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py` | 29 |
| `ToolEnvelope` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py` | 39 |
| `ToolMeta` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py` | 60 |
| `ToolResult` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_envelope.py` | 69 |
| `LLMToolCall` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | 19 |
| `LLMUsage` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | 50 |
| `LLMResponse` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | 56 |
| `ParsedChunk` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/parsed_document.py` | 8 |
| `ParsedDocument` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/parsed_document.py` | 21 |
| `OntologyContext` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/ontology_context.py` | 7 |
| `run` | Function | `apps/backend/tests/services/test_tool_runtime.py` | 55 |
| `test_citation_and_evidence_construct` | Function | `apps/backend/tests/contracts/test_contracts_smoke.py` | 57 |
| `test_tool_envelope_construct` | Function | `apps/backend/tests/contracts/test_contracts_smoke.py` | 26 |
| `test_tool_constraints_defaults` | Function | `apps/backend/tests/contracts/test_contracts_smoke.py` | 117 |
| `spec` | Function | `apps/backend/src/semantic_reasoning_agent/services/tool_registry.py` | 51 |
| `invoke_tool` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | 49 |
| `test_tool_result_construct` | Function | `apps/backend/tests/contracts/test_contracts_smoke.py` | 40 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Invoke_tool → _utc_now` | cross_community | 4 |
| `Invoke_tool → ToolResult` | cross_community | 4 |
| `Run → ToolResult` | intra_community | 3 |
| `Run → ToolMeta` | intra_community | 3 |
| `Run → Evidence` | cross_community | 3 |
| `Run → CitationAnchor` | cross_community | 3 |
| `Run → Provenance` | cross_community | 3 |
| `Invoke_tool → Get` | cross_community | 3 |
| `Invoke_tool → OntologyContextRef` | cross_community | 3 |
| `Invoke_tool → ToolConstraints` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 5 calls |
| Schemas | 1 calls |

## How to Explore

1. `gitnexus_context({name: "run"})` — see callers and callees
2. `gitnexus_query({query: "contracts"})` — find related execution flows
3. Read key files listed above for implementation details
