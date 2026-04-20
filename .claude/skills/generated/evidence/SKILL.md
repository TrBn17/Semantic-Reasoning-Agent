---
name: evidence
description: "Skill for the Evidence area of Semantic-Reasoning-Agent. 5 symbols across 4 files."
---

# Evidence

5 symbols | 4 files | Cohesion: 89%

## When to Use

- Working with code in `apps/`
- Understanding how GraphView, onSubmit, EvidenceDetailDrawer work
- Modifying evidence-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/evidence/evidence-detail-drawer.tsx` | EvidenceDetailDrawer, formatScore |
| `apps/frontend/components/graph/graph-view.tsx` | GraphView |
| `apps/frontend/components/evidence/evidence-view.tsx` | onSubmit |
| `apps/frontend/src/shared/telemetry/track.ts` | track |

## Entry Points

Start here when exploring this area:

- **`GraphView`** (Function) — `apps/frontend/components/graph/graph-view.tsx:42`
- **`onSubmit`** (Function) — `apps/frontend/components/evidence/evidence-view.tsx:99`
- **`EvidenceDetailDrawer`** (Function) — `apps/frontend/components/evidence/evidence-detail-drawer.tsx:17`
- **`track`** (Function) — `apps/frontend/src/shared/telemetry/track.ts:34`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `GraphView` | Function | `apps/frontend/components/graph/graph-view.tsx` | 42 |
| `onSubmit` | Function | `apps/frontend/components/evidence/evidence-view.tsx` | 99 |
| `EvidenceDetailDrawer` | Function | `apps/frontend/components/evidence/evidence-detail-drawer.tsx` | 17 |
| `track` | Function | `apps/frontend/src/shared/telemetry/track.ts` | 34 |
| `formatScore` | Function | `apps/frontend/components/evidence/evidence-detail-drawer.tsx` | 144 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ontology | 1 calls |

## How to Explore

1. `gitnexus_context({name: "GraphView"})` — see callers and callees
2. `gitnexus_query({query: "evidence"})` — find related execution flows
3. Read key files listed above for implementation details
