# Frontend (Next.js)

Workspace control plane for the Semantic Reasoning Agent. Surfaces include ask (chat + retrieval), documents, evidence, ontology builds/review/publish, and published graph — mapped onto the FastAPI backend.

## Stack

- Next.js 15 (App Router) · React 19 · TypeScript
- Tailwind CSS + shadcn/ui primitives
- TanStack Query (server state) + zustand (workspace / model / retrieval prefs)
- sonner toasts, lucide icons

## Layout

```
app/
  (app)/              # sidebar + header shell
    chat/             # conversation list, message thread, composer, citations drawer
    documents/        # upload, list, detail + jobs
    retrieval/        # search playground
    ontology/         # graph stats
      builds/         # build list + detail (entities/relations/steps tabs, publish)
      review/         # cross-build pending queue
components/
  ui/                 # shadcn primitives
  layout/             # sidebar, header, model-picker, workspace-badge
  chat/ documents/ retrieval/ ontology/
lib/
  api/                # typed client + per-resource modules mirroring backend schemas
  query/ state/       # query-key factory, zustand store
```

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
