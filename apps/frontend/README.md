# Frontend (Next.js)

Workspace control plane for the Semantic Reasoning Agent. Primary product surfaces include ask, documents, evidence, ontology builds/review/publish, graph, `/settings` for provider configuration, and `/agents` for agent profile management. `/tools` remains available only as an internal admin/debug surface for AGENTS.md §9 execution primitives.

## Stack

- Next.js 15 · React 19 · TypeScript
- Tailwind CSS + shadcn/ui primitives
- TanStack Query (server state) + zustand (workspace / profile preferences)
- sonner toasts, lucide icons

## Layout

```text
src/app/
  ask/                # chat thread, composer, grounded retrieval toggle
  documents/          # upload, list, detail + jobs
  ontology/           # builds + review + published graph
  graph/              # Cytoscape explorer
  settings/           # providers, readiness, workspace model defaults
  agents/             # agent profiles, capability presets, knowledge packs
  tools/              # admin/debug tool registry + invoke dialog
components/
  ui/                 # shadcn primitives
  layout/             # sidebar, header, workspace controls
  chat/ documents/ ontology/ graph/ tools/
  settings/           # provider settings surface
  agents/             # agent management surface
lib/
  api/                # typed clients bound to canonical backend contracts
  query/ state/       # query-key factory, zustand store
src/shared/
  capabilities/       # feature flags for gated routes
  i18n/               # en + vi dictionaries
```

## Surfaces

| Route | Status | Backend |
|-------|--------|---------|
| `/` (Home) | shipped | — |
| `/ask` | shipped | `POST /api/v1/chat/messages` |
| `/documents` | shipped | `/api/v1/documents*` |
| `/ontology/*` | shipped | `/api/v1/ontology/*` |
| `/graph` | shipped | `GET /api/v1/ontology/graph` |
| `/settings` | shipped | `/api/v1/settings`, `/api/v1/settings/models` |
| `/agents` | shipped | `/api/v1/agents/profiles*`, `/api/v1/agent-capabilities/*`, `/api/v1/knowledge-packs*` |
| `/tools` | internal/admin only | `GET /api/v1/tools`, `POST /api/v1/tools/{name}/invoke` |
| `/workflows`, `/artifacts`, `/connectors` | gated off via `useCapabilities()` until backend lands |

## Information architecture

- `/settings` is limited to provider/API key setup, provider readiness, curated model catalog, and workspace-level model defaults.
- `/agents` owns agent profiles, capability presets, tool policy, knowledge packs, and evidence policy.
- `/tools` is intentionally out of the primary sidebar and should be treated as internal diagnostics, not a product-facing workflow.

## Tool registry surface

`/tools` lists every registered `ToolSpec` with family, risk level, capabilities, timeout, side-effect level, and version. Each row exposes an **Invoke** dialog that:

- builds a `StandardToolInput` envelope with a fresh `call_id` and `task_id`
- lets the user supply `workspace_id`, `task_type`, and tool arguments as JSON
- displays the returned `StandardToolOutput` inline with status, latency, trace metadata, and normalized evidence

Shipped tools: `retrieval.internal` and `ontology.lookup`.

## Run locally

1. Start backend + infra from repo root:
   ```powershell
   docker compose up -d postgres redis neo4j
   .venv\Scripts\python.exe apps/backend/serve.py
   .venv\Scripts\python.exe apps/backend/worker/serve.py
   ```
2. Start the frontend:
   ```powershell
   cd apps/frontend
   npm install
   npm run dev
   ```
3. Open `http://localhost:3000`.

Point at a different backend by setting `NEXT_PUBLIC_API_BASE_URL` or `INTERNAL_API_BASE_URL`.

## Scripts

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run typecheck`
- `npm run lint`
