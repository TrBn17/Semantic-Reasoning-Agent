---
name: tools
description: "Skill for the Tools area of Semantic-Reasoning-Agent. 4 symbols across 1 files."
---

# Tools

4 symbols | 1 files | Cohesion: 86%

## When to Use

- Working with code in `apps/`
- Understanding how ToolInvokeDialog, handleSubmit work
- Modifying tools-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/tools/tool-invoke-dialog.tsx` | ToolInvokeDialog, handleSubmit, defaultArgumentsFor, parseJson |

## Entry Points

Start here when exploring this area:

- **`ToolInvokeDialog`** (Function) — `apps/frontend/components/tools/tool-invoke-dialog.tsx:34`
- **`handleSubmit`** (Function) — `apps/frontend/components/tools/tool-invoke-dialog.tsx:85`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `ToolInvokeDialog` | Function | `apps/frontend/components/tools/tool-invoke-dialog.tsx` | 34 |
| `handleSubmit` | Function | `apps/frontend/components/tools/tool-invoke-dialog.tsx` | 85 |
| `defaultArgumentsFor` | Function | `apps/frontend/components/tools/tool-invoke-dialog.tsx` | 292 |
| `parseJson` | Function | `apps/frontend/components/tools/tool-invoke-dialog.tsx` | 302 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ontology | 1 calls |

## How to Explore

1. `gitnexus_context({name: "ToolInvokeDialog"})` — see callers and callees
2. `gitnexus_query({query: "tools"})` — find related execution flows
3. Read key files listed above for implementation details
