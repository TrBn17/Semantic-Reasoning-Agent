---
name: llm
description: "Skill for the Llm area of Semantic-Reasoning-Agent. 11 symbols across 4 files."
---

# Llm

11 symbols | 4 files | Cohesion: 62%

## When to Use

- Working with code in `apps/`
- Understanding how test_tool_spec_serialization, run, to_anthropic_tool work
- Modifying llm-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | _get_client, run, _to_anthropic_tool_choice, _to_anthropic_messages |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | _get_client, run, _to_openai_tool_choice, _to_openai_messages |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_spec.py` | to_anthropic_tool, to_openai_tool |
| `apps/backend/tests/contracts/test_contracts_smoke.py` | test_tool_spec_serialization |

## Entry Points

Start here when exploring this area:

- **`test_tool_spec_serialization`** (Function) — `apps/backend/tests/contracts/test_contracts_smoke.py:125`
- **`run`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py:56`
- **`to_anthropic_tool`** (Function) — `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_spec.py:54`
- **`to_openai_tool`** (Function) — `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_spec.py:62`
- **`run`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py:56`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `test_tool_spec_serialization` | Function | `apps/backend/tests/contracts/test_contracts_smoke.py` | 125 |
| `run` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | 56 |
| `to_anthropic_tool` | Function | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_spec.py` | 54 |
| `to_openai_tool` | Function | `apps/backend/src/semantic_reasoning_agent/domain/contracts/tool_spec.py` | 62 |
| `run` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | 56 |
| `_get_client` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | 45 |
| `_to_anthropic_tool_choice` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | 86 |
| `_to_anthropic_messages` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | 98 |
| `_get_client` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | 45 |
| `_to_openai_tool_choice` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | 84 |
| `_to_openai_messages` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | 90 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Contracts | 2 calls |
| Services | 1 calls |

## How to Explore

1. `gitnexus_context({name: "test_tool_spec_serialization"})` — see callers and callees
2. `gitnexus_query({query: "llm"})` — find related execution flows
3. Read key files listed above for implementation details
