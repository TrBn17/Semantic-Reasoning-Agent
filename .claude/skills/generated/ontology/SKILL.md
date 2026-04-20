---
name: ontology
description: "Skill for the Ontology area of Semantic-Reasoning-Agent. 58 symbols across 37 files."
---

# Ontology

58 symbols | 37 files | Cohesion: 95%

## When to Use

- Working with code in `apps/`
- Understanding how WorkflowRegistryView, ToolsTable, TaskRunsView work
- Modifying ontology-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/frontend/components/agents/agent-builder-view.tsx` | profileToDraft, AgentBuilderView, RoutingCard, PreviewPanel, StatusLine |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/ontology/llm_extractor.py` | _LLMExtraction, extract_ontology_candidates, _invoke_anthropic, _parse_payload, _to_domain_result |
| `apps/frontend/components/tools/tools-table.tsx` | ToolsTable, ToolRow, RiskBadge |
| `apps/frontend/components/tools/tool-invoke-dialog.tsx` | SchemaHint, InvokeResult, StatusBadge |
| `apps/backend/src/semantic_reasoning_agent/domain/ontology/models.py` | ExtractedEntity, ExtractedRelation, ExtractionResult |
| `apps/frontend/components/workflows/workflow-registry-view.tsx` | WorkflowRegistryView, translateRunStatus |
| `apps/frontend/components/tasks/task-runs-view.tsx` | TaskRunsView, translateRunStatus |
| `apps/frontend/components/tasks/task-detail-view.tsx` | TaskDetailView, translateRunStatus |
| `apps/frontend/components/ontology/new-build-dialog.tsx` | NewBuildDialog, toggleSelection |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/ontology/llm_prompts.py` | build_open_domain_prompt, _format_list |

## Entry Points

Start here when exploring this area:

- **`WorkflowRegistryView`** (Function) — `apps/frontend/components/workflows/workflow-registry-view.tsx:24`
- **`ToolsTable`** (Function) — `apps/frontend/components/tools/tools-table.tsx:21`
- **`TaskRunsView`** (Function) — `apps/frontend/components/tasks/task-runs-view.tsx:34`
- **`TaskDetailView`** (Function) — `apps/frontend/components/tasks/task-detail-view.tsx:22`
- **`NewBuildDialog`** (Function) — `apps/frontend/components/ontology/new-build-dialog.tsx:25`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `ExtractedEntity` | Class | `apps/backend/src/semantic_reasoning_agent/domain/ontology/models.py` | 7 |
| `ExtractedRelation` | Class | `apps/backend/src/semantic_reasoning_agent/domain/ontology/models.py` | 20 |
| `ExtractionResult` | Class | `apps/backend/src/semantic_reasoning_agent/domain/ontology/models.py` | 33 |
| `EmergentSchema` | Class | `apps/backend/src/semantic_reasoning_agent/tools/ontology/schema_registry.py` | 8 |
| `WorkflowRegistryView` | Function | `apps/frontend/components/workflows/workflow-registry-view.tsx` | 24 |
| `ToolsTable` | Function | `apps/frontend/components/tools/tools-table.tsx` | 21 |
| `TaskRunsView` | Function | `apps/frontend/components/tasks/task-runs-view.tsx` | 34 |
| `TaskDetailView` | Function | `apps/frontend/components/tasks/task-detail-view.tsx` | 22 |
| `NewBuildDialog` | Function | `apps/frontend/components/ontology/new-build-dialog.tsx` | 25 |
| `toggleSelection` | Function | `apps/frontend/components/ontology/new-build-dialog.tsx` | 90 |
| `IngestFilesDialog` | Function | `apps/frontend/components/ontology/ingest-files-dialog.tsx` | 22 |
| `GraphStats` | Function | `apps/frontend/components/ontology/graph-stats.tsx` | 23 |
| `CrossBuildReview` | Function | `apps/frontend/components/ontology/cross-build-review.tsx` | 5 |
| `BuildTable` | Function | `apps/frontend/components/ontology/build-table.tsx` | 12 |
| `BuildDetail` | Function | `apps/frontend/components/ontology/build-detail.tsx` | 7 |
| `WorkspaceBadge` | Function | `apps/frontend/components/layout/workspace-badge.tsx` | 11 |
| `useRouteTransition` | Function | `apps/frontend/components/layout/route-transition-provider.tsx` | 90 |
| `LanguageSwitcher` | Function | `apps/frontend/components/layout/language-switcher.tsx` | 5 |
| `AppHeader` | Function | `apps/frontend/components/layout/app-header.tsx` | 7 |
| `UploadDialog` | Function | `apps/frontend/components/documents/upload-dialog.tsx` | 24 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Extract_ontology_candidates → _format_list` | intra_community | 3 |
| `Extract_ontology_candidates → Create` | intra_community | 3 |
| `Extract_ontology_candidates → _LLMExtraction` | intra_community | 3 |

## How to Explore

1. `gitnexus_context({name: "WorkflowRegistryView"})` — see callers and callees
2. `gitnexus_query({query: "ontology"})` — find related execution flows
3. Read key files listed above for implementation details
