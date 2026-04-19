# Frontend Product & Technical Specification
## Semantic Reasoning Agent Frontend Upgrade Blueprint
### Phiên bản: v1.0
### Trạng thái: Draft for implementation
### Đối tượng: Frontend engineers, full-stack engineers, design/UX, AI coding agents

---

## 1. Mục tiêu tài liệu

Tài liệu này đặc tả kế hoạch nâng cấp frontend cho hệ thống **Semantic Reasoning Agent** theo ba mục tiêu chính:

1. **Tổ chức lại toàn bộ frontend cho sạch, dễ mở rộng, dễ bảo trì**
2. **Thiết kế lại UI/UX để người dùng hiểu hệ thống và thao tác hiệu quả**
3. **Đồng bộ frontend với backend hiện tại và target backend trong `AGENTS.md`**

Tài liệu này **không coi frontend là một app chat đơn thuần**.  
Mục tiêu đúng là xây dựng một **workspace control plane** cho:

- ask / task resolution
- workflows
- tools
- documents
- evidence
- ontology
- graph
- artifacts
- settings / admin

Chat chỉ là **một entrypoint**, không phải trung tâm sản phẩm.

---

## 2. Tóm tắt điều hành

Frontend hiện tại đã vượt qua giai đoạn scaffold rỗng và đã có surface khá đầy đủ cho baseline:

- chat
- agents
- documents
- retrieval
- ontology

Nhưng frontend vẫn đang ở trạng thái **baseline/dev**, chưa phải production-ready, và chưa khớp với kiến trúc backend mục tiêu.

### 2.1. Đánh giá ngắn gọn

Frontend hiện tại có ba vấn đề cốt lõi:

#### (A) Nợ kỹ thuật nền tảng
- build chưa sạch
- typecheck fail
- route gốc `/` khả năng 404
- state hiện tại bị lẫn giữa workspace state và per-screen state
- text/copy/encoding còn dở dang

#### (B) Information architecture chưa đúng trục sản phẩm
Frontend hiện vẫn phản ánh tư duy:
- chat-centric
- retrieval như một màn riêng
- ontology như một slice phụ trợ

Trong khi target backend mới là:
- tool-first
- workflow-centric
- ontology-guided
- task-oriented
- evidence-driven
- artifact-capable

#### (C) UI/UX chưa phản ánh model vận hành thật của hệ thống
Người dùng trong tương lai không chỉ:
- chat
- upload docs
- search retrieval

Họ còn phải:
- giải quyết task
- review evidence
- quản lý ontology builds
- publish graph
- chạy workflow
- theo dõi tool runs
- tạo artifact/report/dashboard

### 2.2. Quyết định chiến lược

Frontend mới phải được định nghĩa là:

> **Knowledge Operations Cockpit / Workspace Control Plane**  
> thay vì một chat app có thêm vài màn phụ.

---

## 3. Căn cứ kiến trúc backend

Frontend phải bám cả hai lớp backend:

### 3.1. Backend hiện tại (as-is)
Backend hiện tại là một **layered modular monolith**, trọng tâm thực thi nằm ở:

- FastAPI entrypoints
- service layer orchestration
- SQLAlchemy/Postgres
- Celery jobs
- optional Neo4j projection

Các API/slice đang thực sự hoạt động:
- chat
- conversations
- documents
- retrieval
- ontology
- models
- agents
- agent_profiles

Đặc điểm quan trọng:
- runtime hiện tại vẫn là **service-centric**
- repositories / ports / domain contracts / tool abstractions đã xuất hiện nhưng chưa phải execution core
- ontology là slice mạnh nhất
- retrieval hiện tại vẫn chủ yếu là Postgres-backed, token-vector based
- graph hiện tại là projection downstream, không phải source of truth

### 3.2. Backend target (AGENTS.md)
Target backend được định nghĩa là:

- tool-first
- workflow-centric
- ontology-guided
- task runtime oriented

Trong mô hình target:
- tools là execution primitives
- workflows là execution plans
- ontology là semantic control layer
- chat chỉ là một entrypoint

Target backend còn mở rộng ra:
- tasks/resolve
- workflows
- tools
- evidence promotion
- artifact generation
- web extract
- MCP invoke

### 3.3. Hàm ý trực tiếp cho frontend

Frontend phải:
- không khóa cứng vào API chat cũ
- không assume output chỉ là assistant text
- không assume ontology chỉ là graph viewer
- không assume retrieval là một màn độc lập
- không assume documents là upload/list đơn giản

Frontend phải chuẩn bị để render các output classes như:
- answer
- task result
- evidence bundle
- review task
- ontology candidates
- graph update request
- artifact

---

## 4. Nguyên tắc thiết kế tổng thể

## 4.1. Product principles

### Principle 1 — Task-first, không chat-first
UI chính phải xoay quanh việc “hệ thống đang giải quyết việc gì”, không chỉ “hệ thống đang trả lời gì”.

### Principle 2 — Evidence-first
Mọi câu trả lời, graph update, ontology candidate, artifact đều phải có provenance/evidence rõ ràng.

### Principle 3 — Progressive disclosure
Người dùng phổ thông không cần thấy tất cả concepts kỹ thuật như tool registry, MCP, workflow graph, semantic normalization.
Những thứ này phải mở dần theo role và context.

### Principle 4 — Reviewable systems
Hệ thống không chỉ generate output; nó còn cần:
- review
- approve
- publish
- re-run
- inspect trace

### Principle 5 — One workspace, nhiều bề mặt công việc
Một workspace phải bao quát:
- ask
- docs
- evidence
- ontology
- graph
- workflows
- artifacts
- admin

### Principle 6 — UI phản ánh đúng backend evolution path
Frontend phải tương thích với:
- backend hiện tại
- backend sắp tới
mà không rewrite UI liên tục.

---

## 5. Mục tiêu UX

Frontend mới phải giúp người dùng trả lời 6 câu hỏi càng nhanh càng tốt:

1. **Tôi đang ở đâu trong workspace này?**
2. **Tôi có thể bắt đầu từ đâu?**
3. **Hệ thống đang xử lý việc gì?**
4. **Kết quả này đến từ đâu?**
5. **Tôi cần review/phê duyệt gì?**
6. **Tôi có thể xuất/publish/tái sử dụng kết quả ở đâu?**

Nếu không trả lời được 6 câu này, frontend sẽ tiếp tục bị cảm giác “nhiều màn nhưng khó hiểu”.

---

## 6. Đánh giá frontend hiện tại

## 6.1. Những gì đã có
Frontend hiện đang dùng:
- Next.js 15 App Router
- React 19
- app shell chung
- typed API layer
- React Query provider
- các màn hình chính cho chat, agents, documents, retrieval, ontology

Điều này có nghĩa:
- nền tảng framework là đúng hướng
- đã có baseline routing
- đã có provider/query structure
- đã có UI surface đủ để tái cấu trúc chứ không cần viết lại từ đầu

## 6.2. Các vấn đề kỹ thuật hiện tại

### Build chưa sạch
`npm run build` compile được bundle nhưng fail ở type-check.

### Store bị lệch trách nhiệm
`message-composer` đang dùng:
- `useRetrieval`
- `topK`
- `setUseRetrieval`
- `setTopK`

nhưng `workspace-store` chỉ còn:
- `workspaceId`
- `preferredAgentProfileId`

Đây là dấu hiệu của việc state model chưa được thiết kế đúng.

### TypeScript config dơ / lệch version
- `ignoreDeprecations: "6.0"` không khớp TS 5.7
- include đang kéo cả `.next/types/**/*.ts`
- generated files cũ có thể đang làm typecheck fail

### Routing chưa hoàn thiện
- Sidebar logo link về `/`
- nhưng `src/app` chưa có `page.tsx`
- route `/` có nguy cơ 404

### Copy / encoding dở dang
- text kiểu `Phase 3 baseline Â· ...`
- nhiều ngôn ngữ phase/internal jargon lộ ra ngoài UI

### Kiến trúc sản phẩm cũ còn in đậm
Frontend vẫn đang phản ánh “Phase 3 baseline” nhiều hơn là backend target mới:
- tasks
- workflows
- tools
- evidence control plane
- artifact/report generation
- ontology-guided execution

---

## 7. Mục tiêu nâng cấp

Ba mục tiêu nâng cấp cụ thể:

## 7.1. Mục tiêu 1 — Làm sạch và tổ chức lại mã nguồn
Kết quả mong muốn:
- dễ tìm code
- dễ mở rộng route
- dễ thay API
- dễ test
- không rò state giữa các feature

## 7.2. Mục tiêu 2 — Làm UI/UX dễ hiểu
Kết quả mong muốn:
- người mới vào hiểu ngay “app này dùng để làm gì”
- không bị ngợp bởi thuật ngữ kỹ thuật
- có dòng chảy công việc rõ ràng
- màn nào cũng trả lời được “next action là gì”

## 7.3. Mục tiêu 3 — Khớp backend hiện tại và target
Kết quả mong muốn:
- tận dụng được API hiện có
- không khóa kiến trúc UI vào backend cũ
- sẵn sàng gắn các endpoint mới như tasks/workflows/tools/artifacts mà không phải redesign toàn bộ

---

## 8. Product model mới

Frontend mới nên được mô hình hóa quanh 8 object chính:

1. **Workspace**
2. **Task**
3. **Workflow**
4. **Tool**
5. **Document**
6. **Evidence**
7. **Ontology/Graph**
8. **Artifact**

Chat chỉ là một trong các cách để tạo ra hoặc điều hướng `Task`.

---

## 9. Information Architecture đề xuất

## 9.1. Sidebar cấp 1

### Work
- Home
- Ask
- Tasks

### Knowledge
- Documents
- Evidence
- Ontology
- Graph

### Automation
- Workflows
- Tools
- Connectors

### Outputs
- Artifacts

### Admin
- Models
- Agent Profiles
- Workspace Settings

## 9.2. Đổi tên menu cho dễ hiểu

- `Chat` → `Ask`
- `Retrieval` → `Evidence` hoặc `Sources`
- `Ontology` có thể hiển thị thành `Knowledge Model` hoặc giữ `Ontology` cho admin
- `Graph` là published/explorer surface
- `Agents` nên phân biệt rõ với `Agent Profiles`
- `Models` nằm dưới settings/admin, không phải top-level action chính cho end-user

## 9.3. Role-aware navigation

### End user / analyst
- Home
- Ask
- Documents
- Artifacts

### Knowledge operator
- Home
- Ask
- Documents
- Evidence
- Ontology
- Graph
- Artifacts

### Admin / engineer
- Home
- Ask
- Tasks
- Documents
- Evidence
- Ontology
- Graph
- Workflows
- Tools
- Connectors
- Settings

---

## 10. Sitemap mục tiêu

```text
/
  -> Home / Workspace Overview

/ask
  -> Ask / task resolution surface

/tasks
  -> Task queue, history, status, traces

/workflows
  -> Workflow catalog

/workflows/[workflowId]
  -> Workflow detail, input form, run history

/documents
  -> Document library

/documents/[documentId]
  -> Document detail, jobs, processing state, provenance

/evidence
  -> Evidence browser, promotion/review

/ontology
  -> Ontology overview, builds, queue, schema

/ontology/builds/[buildId]
  -> Build detail, candidates, review actions

/graph
  -> Graph explorer, published view, provenance navigation

/artifacts
  -> Artifact library, report/dashboard outputs

/tools
  -> Tool registry and capabilities

/connectors
  -> MCP / external integration settings and approval policy

/settings/models
/settings/agent-profiles
/settings/workspace
```

---

## 11. Route-by-route đặc tả

## 11.1. `/` — Home / Workspace Overview

### Mục tiêu
Làm entrypoint mặc định cho toàn bộ app.

### Lý do
- sửa vấn đề `/` có thể 404
- dừng việc coi chat là landing page mặc định
- giúp user hiểu workspace đang “sống” như thế nào

### Nội dung nên có
- quick actions:
  - Ask a question
  - Upload document
  - Run workflow
  - Review ontology
  - Open latest artifact
- cards:
  - Running tasks
  - Recent documents
  - Evidence pending review
  - Ontology builds in progress
  - Latest published graph snapshot
  - Recent artifacts
- activity feed:
  - uploads
  - builds
  - promotions
  - publishes
  - workflow runs

### KPI UX
- user hiểu app trong vòng 30 giây
- không cần vào chat mới thấy giá trị hệ thống

---

## 11.2. `/ask` — Ask / Task Resolution

### Vai trò
Đây là bề mặt hỏi đáp, nhưng phải là **task resolution UI**, không chỉ message bubbles.

### Composer cần có
- input chính
- attachment picker
- mode selector:
  - Internal
  - Web
  - Hybrid
- agent profile selector
- advanced controls:
  - freshness
  - max results
  - evidence strictness
  - allow tool use
  - follow-up mode

### Output cần render được
- textual answer
- cited evidence cards
- trace/tool call timeline
- ontology candidate suggestion
- review escalation
- graph update request
- artifact generated
- warning/conflict status

### Layout đề xuất
- center: conversation/task result stream
- right panel:
  - Evidence
  - Trace
  - Actions
- footer under each result:
  - citations
  - provenance
  - re-run
  - convert to workflow
  - promote evidence

### Quy tắc quan trọng
UI không được assume response chỉ có:
```ts
{ role: "assistant", content: string }
```

Frontend phải hỗ trợ:
```ts
type AskOutput =
  | { kind: "answer"; ... }
  | { kind: "review_task"; ... }
  | { kind: "evidence_bundle"; ... }
  | { kind: "ontology_candidates"; ... }
  | { kind: "artifact"; ... }
  | { kind: "graph_update_request"; ... }
```

---

## 11.3. `/tasks` — Task Center

### Mục tiêu
Hiển thị queue/history/status của các task.

### Chức năng
- list tasks
- filter theo:
  - status
  - type
  - workflow
  - owner
  - time range
- xem detail:
  - task payload
  - related workflow
  - evidence summary
  - output
  - trace
- re-run / clone task

### Tại sao cần
Vì trong backend target, task là execution unit quan trọng hơn conversation.

---

## 11.4. `/workflows` — Workflow Catalog

### Mục tiêu
Hiển thị workflows như first-class backend plans.

### Chức năng
- catalog list
- workflow detail
- input schema summary
- run history
- run now action

### Nhóm workflow đề xuất
- document_ingestion
- retrieval
- ontology_build
- review_publish
- promote_evidence
- generate_artifact

### UI pattern
- cards/list
- status chips
- complexity label
- risk label
- deterministic/agentic badge

---

## 11.5. `/workflows/[workflowId]` — Workflow Detail

### Nội dung
- workflow metadata
- purpose
- input form (typed)
- step graph/timeline
- output contract
- policy/risk info
- previous runs

### Visualization
- timeline cho run history
- node graph cho structure
- expandable logs/trace

---

## 11.6. `/documents` — Document Library

### Chức năng
- upload
- list
- filters
- tags/status
- ingestion state
- reprocess

### Các trạng thái quan trọng
- uploaded
- parsing
- chunking
- embedding
- indexed
- failed
- needs reprocess

### Tại sao màn này phải mạnh
Backend hiện tại đã có:
- upload
- jobs
- reprocess
- parsing
- chunks
- indexing

Đây là một flow thật, không phải màn phụ.

---

## 11.7. `/documents/[documentId]` — Document Detail

### Nội dung
- file metadata
- processing status
- job timeline
- extracted structure summary
- evidence references
- ontology linkage
- reprocess action

### Panel đề xuất
- Overview
- Processing
- Citations / Anchors
- Related evidence
- Related entities

---

## 11.8. `/evidence` — Evidence Control Plane

### Mục tiêu
Đây là một surface quan trọng mới.

### Chức năng
- browse evidence
- filter theo:
  - source type
  - trust score
  - freshness
  - document
  - workflow
  - task
  - promoted / unpromoted
- evidence detail
- promote evidence
- compare evidence conflict
- provenance viewer

### Mỗi evidence card nên có
- title
- source type
- snippet/summary
- score
- trust score
- freshness
- citation anchor
- provenance
- linked entities/relations
- action buttons

### Tại sao cần riêng
Target backend coi evidence là normalized runtime output; frontend phải có nơi để:
- kiểm tra
- review
- promote
- truy nguồn

---

## 11.9. `/ontology` — Ontology Operations

### Tách làm 3 phần chính
1. Builds
2. Review Queue
3. Schema / Dictionary

### Chức năng
- tạo build
- xem build đang chạy
- duyệt candidate entities/relations
- approve / reject / edit
- publish version
- xem version history

### KPI UX
Một knowledge operator phải có thể:
- hiểu build nào đang chạy
- biết candidate nào cần review
- publish snapshot mới
mà không phải chui vào raw logs

---

## 11.10. `/ontology/builds/[buildId]` — Build Detail

### Nội dung
- build metadata
- step status
- candidate entity list
- candidate relation list
- confidence
- provenance
- review actions
- publish action nếu đủ điều kiện

### Tách view
- Summary
- Entities
- Relations
- Trace
- Publish readiness

---

## 11.11. `/graph` — Graph Explorer

### Vai trò
Đây là explorer cho graph đã publish, không phải nơi xử lý toàn bộ ontology workflow.

### Chức năng
- graph browse
- node detail
- edge detail
- provenance navigation
- filter by type/domain/version
- compare versions
- subgraph export

### Kỹ thuật visualization
Nên chuẩn bị cho:
- graph cỡ nhỏ-vừa: Cytoscape.js
- graph lớn: Sigma.js

---

## 11.12. `/artifacts` — Artifact Library

### Vai trò
Màn này rất quan trọng trong target backend.

### Artifact có thể gồm
- dashboard payload
- html report
- export bundle

### Chức năng
- list artifacts
- preview artifact
- provenance sidebar
- export/download
- open related task/workflow/evidence

### Rule UX
Artifact phải thể hiện rõ:
- được tạo từ evidence nào
- version template nào
- workflow nào
- trạng thái approved hay draft

---

## 11.13. `/tools` — Tool Registry

### Mục tiêu
UI dành cho admin/engineer/operator.

### Nội dung
- list tools
- capability metadata
- risk level
- side effect level
- requires confirmation
- timeout
- supports parallel / streaming
- workspace scope

### Lợi ích
- giúp debug runtime
- giúp audit
- giúp người vận hành hiểu hệ thống đang có khả năng gì

---

## 11.14. `/connectors` — Connectors / MCP

### Nội dung
- available integrations
- schema cache/status
- read-only / write access
- permission model
- confirmation gates

### Mục đích
Đây là nơi user/admin hiểu:
- hệ thống có thể gọi tool ngoài nào
- ở mức nguy cơ nào
- cần approval gì

---

## 12. Kiến trúc UI component

Frontend nên được chia thành 4 tầng:

1. **Pages/routes**
2. **Feature modules**
3. **Entities**
4. **Shared/UI infra**

## 12.1. Cấu trúc thư mục đề xuất

```text
src/
  app/
    (workspace)/
      page.tsx
      ask/page.tsx
      tasks/page.tsx
      workflows/page.tsx
      workflows/[workflowId]/page.tsx
      documents/page.tsx
      documents/[documentId]/page.tsx
      evidence/page.tsx
      ontology/page.tsx
      ontology/builds/[buildId]/page.tsx
      graph/page.tsx
      artifacts/page.tsx
      tools/page.tsx
      connectors/page.tsx
      settings/
        models/page.tsx
        agent-profiles/page.tsx
        workspace/page.tsx
    layout.tsx
    providers.tsx

  features/
    ask/
    tasks/
    workflows/
    documents/
    evidence/
    ontology/
    graph/
    artifacts/
    tools/
    connectors/
    settings/

  entities/
    workspace/
    task/
    workflow/
    tool/
    document/
    evidence/
    ontology/
    graph/
    artifact/
    conversation/

  widgets/
    app-shell/
    command-bar/
    right-panel/
    trace-drawer/
    source-viewer/
    status-center/

  shared/
    api/
      generated/
      client/
      adapters/
    query/
    ui/
    hooks/
    lib/
    config/
    utils/
```

## 12.2. Nguyên tắc chia module

### `app/`
- route definitions
- loading/error states
- page composition
- server component boundaries

### `features/`
- use case cụ thể
- form logic
- interaction logic
- page-specific orchestration

### `entities/`
- shared model
- card/detail components tái sử dụng
- adapters từ DTO sang ViewModel

### `widgets/`
- app shell
- sidebar
- topbar
- drawers
- layout regions lớn

### `shared/`
- design system
- API infra
- query helpers
- utils chung

---

## 13. Mapping từ code hiện tại sang cấu trúc mới

## 13.1. Di chuyển logic theo domain

- `components/chat/*` → `features/ask/components/*`
- `components/layout/*` → `widgets/app-shell/*`
- `lib/api/types.ts` → `shared/api/generated/*`
- `lib/state/workspace-store.ts` → `entities/workspace/model/*`
- `providers.tsx` → `app/providers.tsx`

## 13.2. Cấm pattern sau
- page import raw DTO khắp nơi
- feature truy cập global store cho local form state
- `components/` như một nơi gom mọi thứ không phân loại
- UI component gọi API trực tiếp không qua adapter/query layer

---

## 14. State management strategy

## 14.1. Phân tầng state

### (1) Server state
Dùng TanStack Query cho:
- fetch
- cache
- invalidation
- mutations
- polling/refetch
- optimistic update khi phù hợp

### (2) Route state
Dùng URL/search params cho:
- filters
- tab
- sort
- selected view
- query mode
- topK
- document scope
- build/version selection

### (3) Local interactive state
Dùng local React state cho:
- input draft
- drawer open
- selected row
- pending form edits
- hover/selection UI

### (4) Session/global state
Dùng Zustand hoặc store nhẹ cho:
- workspaceId
- preferredAgentProfileId
- sidebar collapsed
- right panel mode
- theme / UI preferences

## 14.2. Quy tắc bắt buộc
Không dùng global store cho:
- ask form values
- retrieval toggles per request
- workflow input forms
- page-specific filters
- temporary selection state

---

## 15. API integration architecture

Frontend phải có một **adapter layer** để tách UI khỏi API concrete shape.

## 15.1. Lớp API đề xuất

```text
shared/api/
  generated/        # raw generated/openapi types
  client/           # fetch client
  adapters/         # DTO -> ViewModel / ViewModel -> DTO
```

## 15.2. Lớp feature API

Ví dụ:
```text
features/ask/api/
features/documents/api/
features/ontology/api/
features/artifacts/api/
```

Mỗi feature expose hooks và functions như:
- `useAskTask()`
- `useDocuments()`
- `useDocumentDetail()`
- `useOntologyBuilds()`
- `useArtifactList()`

## 15.3. Compatibility strategy với backend cũ và mới

### Ask
`askApi.resolveTask()`

#### Hiện tại
Có thể map từ:
- chat/messages
- retrieval/search
- conversation metadata

#### Tương lai
Map sang:
- `POST /api/v1/tasks/resolve`

### Workflows
#### Hiện tại
Feature gated hoặc mock disabled state

#### Tương lai
Map sang:
- `GET /api/v1/workflows`
- `POST /api/v1/workflows/{id}/run`

### Tools
#### Hiện tại
disabled / not available

#### Tương lai
Map sang:
- `GET /api/v1/tools`

### Artifacts
#### Hiện tại
disabled / placeholder

#### Tương lai
Map sang:
- `POST /api/v1/artifacts/generate`

### Evidence
#### Hiện tại
assemble từ retrieval results / doc anchors / ontology provenance

#### Tương lai
map trực tiếp sang unified evidence contract

---

## 16. ViewModel contracts đề xuất

Frontend không nên phụ thuộc trực tiếp vào raw API DTO.  
Cần chuẩn hóa các ViewModel sau:

### 16.1. TaskRunViewModel
```ts
type TaskRunViewModel = {
  id: string;
  type: string;
  title: string;
  status: "queued" | "running" | "completed" | "failed" | "needs_review";
  startedAt?: string;
  finishedAt?: string;
  workflowName?: string;
  summary?: string;
  outputs: TaskOutputViewModel[];
};
```

### 16.2. EvidenceItemViewModel
```ts
type EvidenceItemViewModel = {
  id: string;
  sourceType: string;
  title: string;
  summary?: string;
  contentSnippet?: string;
  score?: number;
  trustScore?: number;
  freshnessTs?: string;
  citationLabel?: string;
  locator?: string;
  documentId?: string;
  uri?: string;
  provenanceSummary?: string;
  relatedEntityIds?: string[];
  relatedRelationIds?: string[];
  promoted?: boolean;
};
```

### 16.3. OntologyReviewItemViewModel
```ts
type OntologyReviewItemViewModel = {
  id: string;
  buildId: string;
  itemType: "entity" | "relation";
  label: string;
  candidateType?: string;
  confidence?: number;
  status: "pending" | "approved" | "rejected" | "edited";
  provenanceSummary?: string;
};
```

### 16.4. WorkflowViewModel
```ts
type WorkflowViewModel = {
  id: string;
  name: string;
  description: string;
  category: string;
  executionMode: "deterministic" | "dynamic";
  riskLevel?: "low" | "medium" | "high";
  inputSchemaSummary?: string[];
  outputKinds?: string[];
  available: boolean;
};
```

### 16.5. ArtifactViewModel
```ts
type ArtifactViewModel = {
  id: string;
  kind: "dashboard_payload" | "html_report" | "export_bundle";
  title: string;
  status: "draft" | "ready" | "published";
  createdAt: string;
  templateVersion?: string;
  relatedTaskId?: string;
  relatedWorkflowId?: string;
  evidenceCount?: number;
};
```

---

## 17. Design system & interaction model

## 17.1. Tone thiết kế
- calm
- analytical
- trustworthy
- review-friendly
- evidence-centric

Không nên theo kiểu:
- “AI magic toy”
- quá nhiều hiệu ứng
- chat bubble màu mè
- terminal quá kỹ thuật với user phổ thông

## 17.2. UI primitives cần chuẩn hóa
- cards
- data tables
- filters/search bars
- tabs
- drawers
- inspectors/detail panels
- status badges
- confidence chips
- provenance chips
- trace timeline
- approval action bars

## 17.3. Color semantics
- neutral: default info
- blue: informational / active
- amber: needs review / caution
- red: error / failed / destructive
- green: approved / published
- purple (nếu dùng): ontology / semantic layer

## 17.4. Trạng thái bắt buộc cho mọi màn
- loading
- empty
- error
- partial
- success
- stale
- needs review

---

## 18. UX patterns cốt lõi

## 18.1. Right-panel pattern
Nhiều màn nên có right panel chuẩn hóa với 3 tab:
- Evidence
- Trace
- Actions

Áp dụng cho:
- Ask
- Task detail
- Workflow run detail
- Ontology build detail
- Artifact preview

## 18.2. Drill-down provenance
Mọi object phải có đường đi:
- Answer → Evidence
- Evidence → Source document / web page / graph ref
- Ontology candidate → Evidence
- Artifact → Task / Workflow / Evidence
- Graph node → Ontology version / Evidence

## 18.3. Action bar cho reviewable object
Các object reviewable như:
- evidence
- ontology candidate
- publish request
- artifact draft

nên có action bar thống nhất:
- approve
- reject
- edit
- publish
- rerun
- open source

## 18.4. Status center
Một widget hoặc tray chung hiển thị:
- running tasks
- document jobs
- ontology builds
- failures
- completed actions

---

## 19. Công nghệ khuyến nghị

## 19.1. Nền tảng chính
Giữ:
- Next.js 15 App Router
- React 19
- TypeScript
- TanStack Query

Lý do:
- phù hợp cho hybrid rendering
- server/client component boundaries rõ
- hỗ trợ streaming / suspense / actions
- phù hợp với dashboard + ops surfaces

## 19.2. Graph/workflow UI
- **React Flow** cho workflows / step graphs / node editors
- **Cytoscape.js** cho graph explorer vừa phải
- **Sigma.js** nếu graph lớn cần WebGL performance

## 19.3. Markdown / AI report authoring
### Đề xuất
- **Markdoc** cho template artifact/report có schema và versioning tốt
- **MDXEditor** hoặc **Tiptap Markdown** cho editable narrative/reporting surfaces
- Không dùng raw textarea markdown cho analyst/admin flows

## 19.4. Tables / data grids
Có thể dùng:
- TanStack Table cho flexibility
- hoặc data table components nếu design system đã có

## 19.5. Charts
Dùng thư viện chart nhẹ, ưu tiên:
- Recharts cho dashboard nhanh
- hoặc ECharts nếu cần advanced explorer

---

## 20. Accessibility & internationalization

## 20.1. Accessibility
Bắt buộc:
- keyboard navigation
- focus states rõ
- semantic headings
- aria cho drawers/tabs/tables
- color contrast phù hợp
- screen-reader labels cho status badges/actions

## 20.2. I18n
Nếu sản phẩm hướng tới đội dùng tiếng Việt + tiếng Anh:
- tách copy ra file/messages layer
- tránh hardcode text trong component
- tránh lẫn tiếng Anh kỹ thuật thô trên UI end-user

---

## 21. Kế hoạch xử lý kỹ thuật ngay lập tức

## 21.1. Sprint 0 — Stabilize baseline

### Việc bắt buộc
1. tạo `src/app/page.tsx`
2. sửa sidebar link `/`
3. dọn `workspace-store`
4. gỡ retrieval options khỏi global store
5. sửa `message-composer`
6. dọn `tsconfig.json`
7. xóa dependency vào `.next/types` cũ
8. sửa encoding lỗi
9. dọn copy “Phase 3 baseline”
10. khóa lại CI:
   - lint
   - typecheck
   - build

### Definition of done
- `npm run build` pass
- `npm run typecheck` pass
- route `/` hoạt động
- không còn runtime/type coupling sai giữa store và composer

---

## 22. Kế hoạch tái cấu trúc mã nguồn

## 22.1. Sprint 1 — Restructure src

### Mục tiêu
- đưa code về cấu trúc domain/feature rõ ràng
- tách app shell khỏi business features
- dựng adapter layer

### Việc cần làm
- tạo folder `features/`, `entities/`, `widgets/`, `shared/`
- di chuyển dần components cũ
- tạo typed ViewModel layer
- chuẩn hóa hooks/query keys
- tạo route-level loading/error pages

### Definition of done
- không còn `components/` là thùng rác
- mỗi route có feature owner rõ ràng
- DTO không leak trực tiếp khắp app

---

## 23. Kế hoạch UI/UX rollout

## 23.1. Sprint 2 — Home + Ask + Documents
Ưu tiên các surface có giá trị tức thời:
- Home
- Ask
- Documents
- Document detail

## 23.2. Sprint 3 — Evidence + Ontology
Đây là bước chuyển tư duy từ doc/retrieval sang evidence/knowledge ops:
- Evidence browser
- Ontology overview
- Build detail
- Review queue

## 23.3. Sprint 4 — Graph + Artifacts
- Graph explorer
- Artifact library
- Artifact preview

## 23.4. Sprint 5 — Tasks + Workflows + Tools
Triển khai khi backend control-plane APIs bắt đầu sẵn sàng:
- Tasks
- Workflows
- Workflow detail/run
- Tools
- Connectors

---

## 24. Capability gating strategy

Không phải feature nào cũng có backend ngay từ đầu.  
Frontend cần dùng **capability gates** thay vì hardcode hoặc fake đầy đủ.

Ví dụ:
- `tasksControlPlaneAvailable`
- `workflowRunsAvailable`
- `toolRegistryAvailable`
- `artifactsAvailable`
- `evidencePromotionAvailable`
- `mcpAvailable`

UI behavior:
- available → full feature
- planned → disabled with explanatory state
- unavailable → hidden theo role/context

---

## 25. Backend compatibility strategy

## 25.1. Với backend hiện tại
Frontend có thể triển khai ngay:
- Home
- Ask (trên chat/retrieval hiện có)
- Documents
- Ontology overview/build detail/review
- Graph
- Models
- Agent Profiles

## 25.2. Với backend target
Frontend phải chuẩn bị adapter để cắm:
- tasks/resolve
- workflows
- tools
- evidence promotions
- artifacts/generate
- web/extract
- mcp/invoke

## 25.3. Quy tắc tương thích
UI contract phải ổn định hơn API contract.  
Khi backend đổi endpoint hoặc shape, ta đổi adapter, không đổi toàn bộ feature UI.

---

## 26. Testing strategy

## 26.1. Unit tests
- adapters
- formatters
- view models
- local state hooks
- utility functions

## 26.2. Integration tests
- query hooks
- ask flow
- document upload flow
- ontology review actions

## 26.3. E2E tests
- open workspace home
- ask question
- upload document
- review ontology candidate
- open graph
- open artifact

## 26.4. Visual regression
Quan trọng cho:
- sidebar
- cards
- data tables
- inspector drawers
- graph/workflow canvases

---

## 27. Telemetry & product analytics

Frontend nên đo các hành vi sau:
- ask started / completed
- evidence panel opened
- source opened
- task rerun
- ontology candidate reviewed
- build published
- artifact opened/exported
- workflow run started/completed

Mục đích:
- biết user đang dùng surface nào thật
- tối ưu IA và onboarding
- phát hiện dead features

---

## 28. Security & permission UX

Frontend phải chuẩn bị cho role/policy model:

### Các level hiển thị
- read-only
- review
- approve/publish
- admin/configure

### Những action cần confirmation
- publish graph
- approve batch
- reprocess large document set
- run write-capable connector/tool
- destructive admin settings

### UX rule
Không chỉ disable nút.
Phải nói rõ:
- vì sao không được phép
- role nào cần có
- state nào đang thiếu

---

## 29. Những điều không được làm

1. Không giữ `/chat` làm default home
2. Không để state form nằm trong workspace global store
3. Không để route gắn chặt vào DTO backend hiện tại
4. Không expose internal phase language ra UI
5. Không coi ontology chỉ là graph view
6. Không coi retrieval là product surface cuối cùng
7. Không thiết kế artifact như output text ngẫu hứng không provenance
8. Không thêm nhiều màn control-plane nhưng thiếu entrypoint rõ ràng cho user thường
9. Không xây workflow/tool pages hoàn toàn mock mà không có capability gating
10. Không tiếp tục giữ cấu trúc `components + lib + pages` thiếu domain ownership

---

## 30. Danh sách quyết định kiến trúc chính

### AD-01
Frontend được định vị là **workspace control plane**, không phải chat app.

### AD-02
Route `/` là Home/Overview bắt buộc.

### AD-03
Navigation mới chia theo:
- Work
- Knowledge
- Automation
- Outputs
- Admin

### AD-04
State management phân lớp:
- server state
- route state
- local state
- lightweight session state

### AD-05
Global store không chứa per-form state.

### AD-06
UI dựa trên ViewModel contracts, không phụ thuộc raw DTO.

### AD-07
Feature modules theo domain thay vì thùng `components/` chung.

### AD-08
Evidence là first-class UI surface.

### AD-09
Ontology workflow bao gồm:
- build
- review
- publish
chứ không chỉ graph visualize.

### AD-10
Artifacts là first-class output surface.

---

## 31. Backlog thực thi ưu tiên cao

## P0 — Ngay lập tức
- fix build/typecheck
- tạo home route
- sửa store/composer mismatch
- dọn tsconfig
- dọn encoding/copy

## P1 — Tái cấu trúc
- dựng cấu trúc thư mục mới
- adapter layer
- view models
- app shell chuẩn hóa

## P2 — Product surfaces cốt lõi
- Home
- Ask
- Documents
- Document detail

## P3 — Knowledge ops
- Evidence
- Ontology
- Build detail
- Review queue

## P4 — Output & explorer
- Graph
- Artifacts

## P5 — Future control plane
- Tasks
- Workflows
- Tools
- Connectors

---

## 32. Definition of success

Frontend upgrade được coi là thành công khi đạt các tiêu chí sau:

### Kỹ thuật
- build xanh
- typecheck xanh
- cấu trúc code rõ
- feature ownership rõ
- API adapters tách biệt tốt
- thêm route mới không gây hỗn loạn import/state

### UX
- user hiểu app trong 30 giây đầu
- ask flow có evidence/provenance dễ truy
- ontology review dễ thao tác
- document processing dễ theo dõi
- artifact dễ mở và xuất

### Kiến trúc
- frontend khớp backend hiện tại
- không lệch backend target
- cắm được tasks/workflows/tools/artifacts về sau mà không redesign toàn bộ

---

## 33. Kết luận

Frontend hiện tại không cần rewrite từ đầu, nhưng chắc chắn cần **re-architecture có chủ đích**.

Hướng đi đúng là:

1. **stabilize baseline**
2. **restructure src theo domain + features**
3. **đổi product model từ chat-centric sang control-plane**
4. **đưa evidence / ontology / workflow / artifact thành first-class surfaces**
5. **thiết kế API adapter layer để sống được qua quá trình backend nâng cấp**

Nói ngắn gọn:

> Frontend mới phải trở thành **knowledge operations cockpit**  
> cho một hệ thống **tool-first, workflow-centric, ontology-guided**,  
> chứ không chỉ là một giao diện chat có thêm vài tab.

---

## 34. Phụ lục A — Đề xuất cấu trúc triển khai component theo màn

### Home
- `WorkspaceHero`
- `QuickActions`
- `RunningTasksCard`
- `RecentDocumentsCard`
- `EvidenceQueueCard`
- `OntologyBuildsCard`
- `RecentArtifactsCard`
- `ActivityFeed`

### Ask
- `AskComposer`
- `ModeSelector`
- `AgentProfilePicker`
- `AskResultStream`
- `EvidencePanel`
- `TracePanel`
- `ActionPanel`
- `CitationList`

### Documents
- `DocumentTable`
- `UploadDialog`
- `DocumentFilters`
- `DocumentStatusBadge`

### Document detail
- `DocumentOverview`
- `ProcessingTimeline`
- `ChunkAnchorList`
- `RelatedEvidencePanel`
- `RelatedEntitiesPanel`

### Evidence
- `EvidenceTable`
- `EvidenceFilters`
- `EvidenceCard`
- `EvidenceDetailDrawer`
- `ProvenancePanel`
- `PromotionActionBar`

### Ontology
- `OntologyBuildTable`
- `ReviewQueue`
- `SchemaSummary`
- `VersionHistory`

### Build detail
- `BuildSummary`
- `BuildStepsTimeline`
- `CandidateEntityTable`
- `CandidateRelationTable`
- `ReviewInspector`
- `PublishReadinessPanel`

### Graph
- `GraphCanvas`
- `NodeInspector`
- `EdgeInspector`
- `VersionCompareToolbar`

### Artifacts
- `ArtifactTable`
- `ArtifactPreview`
- `ArtifactMetadataPanel`
- `ArtifactProvenanceSidebar`

### Workflows
- `WorkflowCatalog`
- `WorkflowCard`
- `WorkflowRunForm`
- `WorkflowRunTimeline`

### Tools
- `ToolRegistryTable`
- `ToolDetailDrawer`
- `RiskBadge`
- `CapabilityTags`

---

## 35. Phụ lục B — Đề xuất query keys

```ts
const queryKeys = {
  workspace: ["workspace"],
  conversations: ["conversations"],
  askRuns: ["ask-runs"],
  tasks: ["tasks"],
  taskDetail: (id: string) => ["tasks", id],
  documents: ["documents"],
  documentDetail: (id: string) => ["documents", id],
  documentJobs: (id: string) => ["documents", id, "jobs"],
  evidence: ["evidence"],
  evidenceDetail: (id: string) => ["evidence", id],
  ontologyBuilds: ["ontology-builds"],
  ontologyBuildDetail: (id: string) => ["ontology-builds", id],
  ontologyEntities: (id: string) => ["ontology-builds", id, "entities"],
  ontologyRelations: (id: string) => ["ontology-builds", id, "relations"],
  graph: ["graph"],
  artifacts: ["artifacts"],
  workflows: ["workflows"],
  tools: ["tools"],
  models: ["models"],
  agentProfiles: ["agent-profiles"],
};
```

---

## 36. Phụ lục C — Chuẩn rollout copy/UI language

### Dùng
- Ask
- Evidence
- Review
- Publish
- Build
- Run workflow
- Knowledge graph
- Artifact
- Source
- Provenance

### Tránh
- baseline
- phase 3
- agent loop
- raw ontology jargon với user phổ thông
- “magic AI” language

---

## 37. Phụ lục D — Tài liệu nguồn tham chiếu nội bộ

Tài liệu này được xây dựng dựa trên hai nguồn backend chính:

1. `AGENTS.md`
   - target-state backend blueprint
   - tool-first / workflow-centric / ontology-guided
   - task/workflow/tool/evidence/artifact contracts

2. `BE architecture.md`
   - current as-is backend architecture
   - service-centric FastAPI/Celery/Postgres/Neo4j topology
   - active API families và execution flows

