# API Usage Report - Cloudflare E2E Test

Date: 2026-04-23  
Target API: `http://localhost:8000`  
Workspace: `workspace-demo`

## Scope

Requested scenario:

1. Upload document for ontology extraction
2. Extract ontology
3. Publish ontology to graph
4. Register graph as user tools
5. Query via AI and return correct result
6. End

Requested models:

- Chat/Ontology model: `@cf/moonshotai/kimi-k2.5`
- Ontology embedding model: `bge-large-en-v1.5`

## Configuration Performed

### Cloudflare provider enablement

- Endpoint: `PUT /api/v1/settings`
- Result: `200 OK`
- Cloudflare provider status after update: `enabled=true`, `ready=true`

### Cloudflare model catalog check

- Endpoint: `GET /api/v1/settings/providers/cloudflare/models?workspace_id=workspace-demo`
- Result: `200 OK`
- Model list count: `55`
- Contains requested model `@cf/moonshotai/kimi-k2.5`: `true`

## E2E Execution Results

### Step 1 - Upload test document

- Endpoint: `POST /api/v1/documents/upload`
- File used: `test_doc/sample_buildings.csv`
- Ingestion mode: `ontology`
- Result: `201 Created`
- Document ID: `f2226008-6d11-486a-b044-c45cb3219704`

### Step 2 - Ontology extraction build

- Endpoint: `POST /api/v1/ontology/builds`
- Payload provider/model: `cloudflare` + `@cf/moonshotai/kimi-k2.5`
- Result: `201 Created`
- Build ID: `31755a17-e5be-4a7b-b511-7f41c8c52b8f`

Build state observations:

- `classify_document_domain`: completed
- `extract_entities`: stuck in `running`
- Build overall status stayed `running` beyond polling window

Worker logs confirm outbound Cloudflare call:

- `POST https://api.cloudflare.com/client/v4/accounts/.../ai/v1/chat/completions -> HTTP/1.1 200 OK`

But build did not transition to `completed` or `failed` afterward.

### Step 3 - Publish ontology graph

- Endpoint: `POST /api/v1/ontology/builds/{build_id}/publish`
- Status: **not executed successfully**
- Reason: build never reached `completed`

Graph read check:

- Endpoint: `GET /api/v1/ontology/graph?workspace_id=workspace-demo`
- Result: `200 OK`
- Published version: `null`
- Entities: `0`
- Relations: `0`

### Step 4 - Register graph tool for users

- Endpoint: `POST /api/v1/search-tools`
- Result: `201 Created`
- Config ID: `fb00b379-668b-4080-9103-f8d9b6b4af7c`
- Tool type: `graph`
- Provider/model: `cloudflare` + `@cf/moonshotai/kimi-k2.5`
- Ready: `true`

Tool run:

- Endpoint: `POST /api/v1/search-tools/{config_id}/run`
- Query: `toa nha tang`
- Result: `200 OK`
- Status: `partial`
- Evidence: `[]`
- Hint: `no_match`

This is consistent with no published ontology graph available.

### Step 5 - AI query validation

Conversation creation:

- Endpoint: `POST /api/v1/conversations`
- Result: `201 Created`

Chat query:

- Endpoint: `POST /api/v1/chat/messages`
- Model: `@cf/moonshotai/kimi-k2.5`
- Result: `500 Internal Server Error`

Observed DB error from logs:

- `insert or update on table "evidence_bundles" violates foreign key constraint "evidence_bundles_task_run_id_fkey"`

This blocks chat result validation for correctness.

## Conclusion

Requested full E2E scenario is **not completed** in current runtime due backend runtime issues:

1. Ontology build hangs at `extract_entities` after Cloudflare request returns `200`
2. Chat endpoint returns `500` due `evidence_bundles` foreign key violation

Because of those blockers:

- Ontology publish to graph cannot complete
- Graph tool can be created but returns `partial/no_match`
- End-user AI answer correctness cannot be validated end-to-end

## Note on embedding model request (`bge-large-en-v1.5`)

During this API-path test, no API contract was found to set ontology embedding model to `bge-large-en-v1.5` for this flow.  
Current retrieval/vector implementation in this codebase appears to use internal token-vector embedding backend rather than external embedding model selection via public API.

## Recommended Next Actions

1. Add timeout/fail-safe around ontology extraction task to avoid indefinite `running`.
2. Trace/fix task run persistence order causing `evidence_bundles_task_run_id_fkey` violation in chat path.
3. Re-run the exact same E2E script after fixes with:
   - `cloudflare/@cf/moonshotai/kimi-k2.5` for chat and ontology extraction
   - explicit embedding model control exposed (if required by product contract).
