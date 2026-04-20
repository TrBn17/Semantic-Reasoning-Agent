---
name: home
description: "Skill for the Home area of Semantic-Reasoning-Agent. 4 symbols across 1 files."
---

# Home

4 symbols | 1 files | Cohesion: 75%

## When to Use

- Working with code in `apps/`
- Understanding how HomeView work
- Modifying home-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/home/home-view.tsx` | HomeView, badgeVariant, translateQuickActionTitle, translateQuickActionDescription |

## Entry Points

Start here when exploring this area:

- **`HomeView`** (Function) — `apps/frontend/components/home/home-view.tsx:48`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `HomeView` | Function | `apps/frontend/components/home/home-view.tsx` | 48 |
| `badgeVariant` | Function | `apps/frontend/components/home/home-view.tsx` | 288 |
| `translateQuickActionTitle` | Function | `apps/frontend/components/home/home-view.tsx` | 305 |
| `translateQuickActionDescription` | Function | `apps/frontend/components/home/home-view.tsx` | 320 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `HomeView → GetCapabilities` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Layout | 1 calls |
| Ontology | 1 calls |

## How to Explore

1. `gitnexus_context({name: "HomeView"})` — see callers and callees
2. `gitnexus_query({query: "home"})` — find related execution flows
3. Read key files listed above for implementation details
