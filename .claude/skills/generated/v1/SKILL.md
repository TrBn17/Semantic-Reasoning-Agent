---
name: v1
description: "Skill for the V1 area of Semantic-Reasoning-Agent. 7 symbols across 3 files."
---

# V1

7 symbols | 3 files | Cohesion: 84%

## When to Use

- Working with code in `apps/`
- Understanding how list_provider_models, list_all_provider_models, list_tools work
- Modifying v1-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py` | DynamicModelResponse, ProviderModelsResponse, list_provider_models, list_all_provider_models |
| `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | list_tools, _spec_to_schema |
| `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | ToolSpecSchema |

## Entry Points

Start here when exploring this area:

- **`list_provider_models`** (Function) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py:36`
- **`list_all_provider_models`** (Function) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py:96`
- **`list_tools`** (Function) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py:39`
- **`DynamicModelResponse`** (Class) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py:13`
- **`ProviderModelsResponse`** (Class) — `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py:24`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DynamicModelResponse` | Class | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py` | 13 |
| `ProviderModelsResponse` | Class | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py` | 24 |
| `ToolSpecSchema` | Class | `apps/backend/src/semantic_reasoning_agent/schemas/tools.py` | 41 |
| `list_provider_models` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py` | 36 |
| `list_all_provider_models` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/provider_models.py` | 96 |
| `list_tools` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | 39 |
| `_spec_to_schema` | Function | `apps/backend/src/semantic_reasoning_agent/entrypoints/v1/tools.py` | 74 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `List_all_provider_models → ProviderModel` | cross_community | 5 |
| `List_all_provider_models → OpenAIModelsClient` | cross_community | 4 |
| `List_all_provider_models → AnthropicModelsClient` | cross_community | 4 |
| `List_provider_models → ProviderModel` | cross_community | 4 |
| `List_provider_models → OpenAIModelsClient` | cross_community | 3 |
| `List_provider_models → AnthropicModelsClient` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 3 calls |

## How to Explore

1. `gitnexus_context({name: "list_provider_models"})` — see callers and callees
2. `gitnexus_query({query: "v1"})` — find related execution flows
3. Read key files listed above for implementation details
