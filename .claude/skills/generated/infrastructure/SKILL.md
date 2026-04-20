---
name: infrastructure
description: "Skill for the Infrastructure area of Semantic-Reasoning-Agent. 25 symbols across 8 files."
---

# Infrastructure

25 symbols | 8 files | Cohesion: 70%

## When to Use

- Working with code in `apps/`
- Understanding how test_echo_returns_user_content_with_system_prefix, test_echo_without_system_uses_plain_prefix, test_echo_required_tool_choice_emits_fake_tool_call work
- Modifying infrastructure-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/tests/infrastructure/test_openai_adapter.py` | _FakeClient, _spec, test_openai_forwards_tool_schema_and_parses_text_reply, test_openai_parses_tool_calls_and_json_arguments, test_openai_encodes_tool_role_and_assistant_tool_calls (+2) |
| `apps/backend/tests/infrastructure/test_echo_adapter.py` | _spec, test_echo_returns_user_content_with_system_prefix, test_echo_without_system_uses_plain_prefix, test_echo_required_tool_choice_emits_fake_tool_call, test_echo_auto_with_tools_does_not_invoke_them |
| `apps/backend/tests/infrastructure/test_anthropic_adapter.py` | _FakeClient, _spec, test_anthropic_forwards_tool_schema_and_parses_text_reply, test_anthropic_parses_tool_use_block, test_anthropic_encodes_tool_result_and_assistant_tool_use |
| `apps/backend/src/semantic_reasoning_agent/ports/llm_adapter.py` | run, legacy_generate_reply, ProviderAdapter |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/echo.py` | EchoAdapter, run |
| `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | LLMMessage |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | AnthropicAdapter |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | OpenAIAdapter |

## Entry Points

Start here when exploring this area:

- **`test_echo_returns_user_content_with_system_prefix`** (Function) — `apps/backend/tests/infrastructure/test_echo_adapter.py:18`
- **`test_echo_without_system_uses_plain_prefix`** (Function) — `apps/backend/tests/infrastructure/test_echo_adapter.py:32`
- **`test_echo_required_tool_choice_emits_fake_tool_call`** (Function) — `apps/backend/tests/infrastructure/test_echo_adapter.py:41`
- **`test_echo_auto_with_tools_does_not_invoke_them`** (Function) — `apps/backend/tests/infrastructure/test_echo_adapter.py:57`
- **`run`** (Function) — `apps/backend/src/semantic_reasoning_agent/ports/llm_adapter.py:26`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `EchoAdapter` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/echo.py` | 16 |
| `LLMMessage` | Class | `apps/backend/src/semantic_reasoning_agent/domain/contracts/llm.py` | 32 |
| `ProviderAdapter` | Class | `apps/backend/src/semantic_reasoning_agent/ports/llm_adapter.py` | 13 |
| `AnthropicAdapter` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/anthropic_adapter.py` | 25 |
| `OpenAIAdapter` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/openai_adapter.py` | 25 |
| `test_echo_returns_user_content_with_system_prefix` | Function | `apps/backend/tests/infrastructure/test_echo_adapter.py` | 18 |
| `test_echo_without_system_uses_plain_prefix` | Function | `apps/backend/tests/infrastructure/test_echo_adapter.py` | 32 |
| `test_echo_required_tool_choice_emits_fake_tool_call` | Function | `apps/backend/tests/infrastructure/test_echo_adapter.py` | 41 |
| `test_echo_auto_with_tools_does_not_invoke_them` | Function | `apps/backend/tests/infrastructure/test_echo_adapter.py` | 57 |
| `run` | Function | `apps/backend/src/semantic_reasoning_agent/ports/llm_adapter.py` | 26 |
| `legacy_generate_reply` | Function | `apps/backend/src/semantic_reasoning_agent/ports/llm_adapter.py` | 40 |
| `run` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/llm/echo.py` | 28 |
| `test_anthropic_forwards_tool_schema_and_parses_text_reply` | Function | `apps/backend/tests/infrastructure/test_anthropic_adapter.py` | 31 |
| `test_anthropic_parses_tool_use_block` | Function | `apps/backend/tests/infrastructure/test_anthropic_adapter.py` | 64 |
| `test_anthropic_encodes_tool_result_and_assistant_tool_use` | Function | `apps/backend/tests/infrastructure/test_anthropic_adapter.py` | 97 |
| `test_openai_forwards_tool_schema_and_parses_text_reply` | Function | `apps/backend/tests/infrastructure/test_openai_adapter.py` | 37 |
| `test_openai_parses_tool_calls_and_json_arguments` | Function | `apps/backend/tests/infrastructure/test_openai_adapter.py` | 73 |
| `test_openai_encodes_tool_role_and_assistant_tool_calls` | Function | `apps/backend/tests/infrastructure/test_openai_adapter.py` | 111 |
| `_FakeClient` | Class | `apps/backend/tests/infrastructure/test_anthropic_adapter.py` | 9 |
| `_FakeClient` | Class | `apps/backend/tests/infrastructure/test_openai_adapter.py` | 20 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Resolve_chat_message → LLMMessage` | cross_community | 4 |
| `Process_document_task → EchoAdapter` | cross_community | 4 |
| `Process_document_task → AnthropicAdapter` | cross_community | 4 |
| `Process_document_task → OpenAIAdapter` | cross_community | 4 |
| `Process_ontology_build_task → EchoAdapter` | cross_community | 4 |
| `Process_ontology_build_task → AnthropicAdapter` | cross_community | 4 |
| `Process_ontology_build_task → OpenAIAdapter` | cross_community | 4 |
| `Run_workflow → LLMMessage` | cross_community | 4 |
| `Get_conversation_service → EchoAdapter` | cross_community | 4 |
| `Get_conversation_service → AnthropicAdapter` | cross_community | 4 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Llm | 6 calls |
| Contracts | 5 calls |
| Services | 3 calls |

## How to Explore

1. `gitnexus_context({name: "test_echo_returns_user_content_with_system_prefix"})` — see callers and callees
2. `gitnexus_query({query: "infrastructure"})` — find related execution flows
3. Read key files listed above for implementation details
