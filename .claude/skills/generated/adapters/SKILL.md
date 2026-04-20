---
name: adapters
description: "Skill for the Adapters area of Semantic-Reasoning-Agent. 9 symbols across 2 files."
---

# Adapters

9 symbols | 2 files | Cohesion: 78%

## When to Use

- Working with code in `apps/`
- Understanding how EvidenceView, retrievalResultToEvidence, citationToEvidence work
- Modifying adapters-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/src/shared/api/adapters/evidence.ts` | retrievalResultToEvidence, citationToEvidence, buildCitationProvenance, publishedEntityToEvidence, candidateEntityToEvidence (+3) |
| `apps/frontend/components/evidence/evidence-view.tsx` | EvidenceView |

## Entry Points

Start here when exploring this area:

- **`EvidenceView`** (Function) — `apps/frontend/components/evidence/evidence-view.tsx:30`
- **`retrievalResultToEvidence`** (Function) — `apps/frontend/src/shared/api/adapters/evidence.ts:13`
- **`citationToEvidence`** (Function) — `apps/frontend/src/shared/api/adapters/evidence.ts:31`
- **`publishedEntityToEvidence`** (Function) — `apps/frontend/src/shared/api/adapters/evidence.ts:103`
- **`candidateEntityToEvidence`** (Function) — `apps/frontend/src/shared/api/adapters/evidence.ts:45`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `EvidenceView` | Function | `apps/frontend/components/evidence/evidence-view.tsx` | 30 |
| `retrievalResultToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 13 |
| `citationToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 31 |
| `publishedEntityToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 103 |
| `candidateEntityToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 45 |
| `candidateRelationToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 63 |
| `publishedRelationToEvidence` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 117 |
| `buildCitationProvenance` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 81 |
| `summarizeProvenance` | Function | `apps/frontend/src/shared/api/adapters/evidence.ts` | 96 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `EvidenceView → GetCapabilities` | cross_community | 3 |
| `EvidenceView → BuildCitationProvenance` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ontology | 1 calls |
| Layout | 1 calls |

## How to Explore

1. `gitnexus_context({name: "EvidenceView"})` — see callers and callees
2. `gitnexus_query({query: "adapters"})` — find related execution flows
3. Read key files listed above for implementation details
