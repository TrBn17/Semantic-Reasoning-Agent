# Frontend (Next.js)

Workspace control plane for the Semantic Reasoning Agent. Surfaces include ask (chat + retrieval), documents, evidence, ontology builds/review/publish, published graph, and — as of 2026-04-20 — the tool registry for AGENTS.md §9 execution primitives.

## Stack

- Next.js 15 (App Router) · React 19 · TypeScript
- Tailwind CSS + shadcn/ui primitives
- TanStack Query (server state) + zustand (workspace / model / retrieval prefs)
- sonner toasts, lucide icons

## Layout

```
src/app/
  ask/                # chat thread, composer, grounded retrieval toggle
  documents/          # upload, list, detail + jobs
  ontology/           # builds + review + published graph
  graph/              # Cytoscape explorer
  tools/              # NEW — AGENTS.md §9 tool registry + invoke dialog
  settings/           # providers, models, agent profiles
components/
  ui/                 # shadcn primitives
  layout/             # sidebar, header, model-picker, workspace-badge
  chat/ documents/ ontology/ graph/ tools/
lib/
  api/                # typed client + per-resource modules mirroring backend schemas
                      #   (tools.ts wraps GET /tools and POST /tools/{name}/invoke)
  query/ state/       # query-key factory, zustand store
src/shared/
  capabilities/       # feature flags (tools now enabled; workflows/tasks deferred)
  i18n/               # en+vi dictionaries
```

## Surfaces

| Route | Status | Backend |
|-------|--------|---------|
| `/` (Home) | shipped | — |
| `/ask` | shipped | `POST /api/v1/chat/messages` |
| `/documents` | shipped | `/api/v1/documents*` |
| `/ontology/*` | shipped | `/api/v1/ontology/*` |
| `/graph` | shipped | `GET /api/v1/ontology/graph` |
| `/tools` | shipped 2026-04-20 | `GET /api/v1/tools`, `POST /api/v1/tools/{name}/invoke` |
| `/settings` | shipped | `/api/v1/agents/*`, `/api/v1/models`, `/api/v1/provider-models` |
| `/workflows`, `/artifacts`, `/connectors` | gated off via `useCapabilities()` until backend lands |

## Tool registry surface (AGENTS.md §9)

`/tools` lists every registered `ToolSpec` with family, risk level, capabilities, timeout, side-effect level, and version. Each row exposes an **Invoke** dialog that:

- builds a `StandardToolInput` envelope with a fresh `call_id` (`crypto.randomUUID()`) and `task_id`,
- lets the user supply `workspace_id`, `task_type`, and tool arguments as JSON (with smart defaults per tool: e.g. `{query, top_k}` for `retrieval.internal`, `{mode}` for `ontology.lookup`),
- displays the returned `StandardToolOutput` inline: status badge (success / partial / failed), latency, truncated `trace_id`, `next_action_hints`, `error_code` / `error_message`, and a scrollable evidence list with source type, citation anchor, and score.

Shipped tools: `retrieval.internal` (wraps `RetrievalService.search`) and `ontology.lookup` (reads published ontology graph).

## Run locally

1. Start backend + infra (from repo root):
   ```powershell
   docker compose up -d postgres redis neo4j
   .venv\Scripts\python.exe apps/backend/serve.py
   .venv\Scripts\python.exe apps/backend/worker/serve.py
   ```
2. Frontend:
   ```powershell
   cd apps/frontend
   npm install
   npm run dev
   ```
3. Open http://localhost:3000.

Point at a different backend by setting `NEXT_PUBLIC_API_BASE_URL` (see `.env.example`).

## Scripts

- `npm run dev` — Next dev server on port 3000
- `npm run build` / `npm run start` — production build
- `npm run typecheck` — `tsc --noEmit`
- `npm run lint`
