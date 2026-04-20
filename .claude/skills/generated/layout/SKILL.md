---
name: layout
description: "Skill for the Layout area of Semantic-Reasoning-Agent. 6 symbols across 4 files."
---

# Layout

6 symbols | 4 files | Cohesion: 77%

## When to Use

- Working with code in `apps/`
- Understanding how IdlePrefetcher, AppSidebar, useCapabilities work
- Modifying layout-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/layout/app-sidebar.tsx` | buildGroups, AppSidebar, isActive |
| `apps/frontend/components/layout/idle-prefetcher.tsx` | IdlePrefetcher |
| `apps/frontend/src/shared/capabilities/useCapabilities.ts` | useCapabilities |
| `apps/frontend/src/shared/capabilities/capabilities.ts` | getCapabilities |

## Entry Points

Start here when exploring this area:

- **`IdlePrefetcher`** (Function) — `apps/frontend/components/layout/idle-prefetcher.tsx:15`
- **`AppSidebar`** (Function) — `apps/frontend/components/layout/app-sidebar.tsx:142`
- **`useCapabilities`** (Function) — `apps/frontend/src/shared/capabilities/useCapabilities.ts:4`
- **`getCapabilities`** (Function) — `apps/frontend/src/shared/capabilities/capabilities.ts:38`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `IdlePrefetcher` | Function | `apps/frontend/components/layout/idle-prefetcher.tsx` | 15 |
| `AppSidebar` | Function | `apps/frontend/components/layout/app-sidebar.tsx` | 142 |
| `useCapabilities` | Function | `apps/frontend/src/shared/capabilities/useCapabilities.ts` | 4 |
| `getCapabilities` | Function | `apps/frontend/src/shared/capabilities/capabilities.ts` | 38 |
| `buildGroups` | Function | `apps/frontend/components/layout/app-sidebar.tsx` | 36 |
| `isActive` | Function | `apps/frontend/components/layout/app-sidebar.tsx` | 216 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `AppSidebar → GetCapabilities` | intra_community | 3 |
| `HomeView → GetCapabilities` | cross_community | 3 |
| `EvidenceView → GetCapabilities` | cross_community | 3 |
| `IdlePrefetcher → GetCapabilities` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ontology | 1 calls |

## How to Explore

1. `gitnexus_context({name: "IdlePrefetcher"})` — see callers and callees
2. `gitnexus_query({query: "layout"})` — find related execution flows
3. Read key files listed above for implementation details
