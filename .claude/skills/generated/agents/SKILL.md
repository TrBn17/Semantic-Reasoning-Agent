---
name: agents
description: "Skill for the Agents area of Semantic-Reasoning-Agent. 7 symbols across 1 files."
---

# Agents

7 symbols | 1 files | Cohesion: 92%

## When to Use

- Working with code in `apps/`
- Understanding how AgentSettingsView, handleSaveSettings work
- Modifying agents-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/agents/agent-settings-view.tsx` | hydrateProviderDrafts, hydrateTaskDrafts, buildSettingsPayload, getProviderPreview, getModelPreview (+2) |

## Entry Points

Start here when exploring this area:

- **`AgentSettingsView`** (Function) — `apps/frontend/components/agents/agent-settings-view.tsx:293`
- **`handleSaveSettings`** (Function) — `apps/frontend/components/agents/agent-settings-view.tsx:488`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `AgentSettingsView` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 293 |
| `handleSaveSettings` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 488 |
| `hydrateProviderDrafts` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 53 |
| `hydrateTaskDrafts` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 75 |
| `buildSettingsPayload` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 84 |
| `getProviderPreview` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 110 |
| `getModelPreview` | Function | `apps/frontend/components/agents/agent-settings-view.tsx` | 146 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Ontology | 1 calls |

## How to Explore

1. `gitnexus_context({name: "AgentSettingsView"})` — see callers and callees
2. `gitnexus_query({query: "agents"})` — find related execution flows
3. Read key files listed above for implementation details
