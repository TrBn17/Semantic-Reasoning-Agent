---
name: domain
description: "Skill for the Domain area of Semantic-Reasoning-Agent. 4 symbols across 1 files."
---

# Domain

4 symbols | 1 files | Cohesion: 100%

## When to Use

- Working with code in `apps/`
- Understanding how DomainError, ToolError, ExtractionError work
- Modifying domain-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/domain/errors.py` | DomainError, ToolError, ExtractionError, WorkflowError |

## Entry Points

Start here when exploring this area:

- **`DomainError`** (Class) — `apps/backend/src/semantic_reasoning_agent/domain/errors.py:3`
- **`ToolError`** (Class) — `apps/backend/src/semantic_reasoning_agent/domain/errors.py:7`
- **`ExtractionError`** (Class) — `apps/backend/src/semantic_reasoning_agent/domain/errors.py:11`
- **`WorkflowError`** (Class) — `apps/backend/src/semantic_reasoning_agent/domain/errors.py:15`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `DomainError` | Class | `apps/backend/src/semantic_reasoning_agent/domain/errors.py` | 3 |
| `ToolError` | Class | `apps/backend/src/semantic_reasoning_agent/domain/errors.py` | 7 |
| `ExtractionError` | Class | `apps/backend/src/semantic_reasoning_agent/domain/errors.py` | 11 |
| `WorkflowError` | Class | `apps/backend/src/semantic_reasoning_agent/domain/errors.py` | 15 |

## How to Explore

1. `gitnexus_context({name: "DomainError"})` — see callers and callees
2. `gitnexus_query({query: "domain"})` — find related execution flows
3. Read key files listed above for implementation details
