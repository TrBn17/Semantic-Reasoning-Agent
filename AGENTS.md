# Tài liệu nghiệp vụ / PRD kỹ thuật
## Hệ thống AI Agent tích hợp Chat, RAG (Qdrant), Ontology + GraphDB, MCP Gateway, Narrative và Dashboard HTML

**Phiên bản:** v1.0  
**Trạng thái:** Draft để triển khai  
**Mục tiêu sử dụng:** Làm tài liệu nền cho đội sản phẩm, đội kỹ thuật và AI coding agent bám vào để phân rã backlog, thiết kế API, UI và triển khai theo phase.

---

## 1. Mục tiêu sản phẩm

Xây dựng một nền tảng AI Agent có giao diện chat tương tự ChatGPT, cho phép người dùng:

1. Trò chuyện với AI trên nhiều LLM khác nhau: **OpenAI, Anthropic, Gemini, Ollama**.
2. Tìm kiếm và trả lời trên dữ liệu tài liệu nội bộ qua **RAG với Qdrant**.
3. Tự động xây dựng và mở rộng **Ontology / Knowledge Graph** từ tài liệu người dùng tải lên.
4. Kết nối tới **MCP từ nhiều nguồn khác nhau** qua một **custom MCP Gateway**.
5. Hiển thị và quản trị ontology qua giao diện đồ thị.
6. Sinh **narrative** và **dashboard HTML** dựa trên ontology/graph để phục vụ phân tích và trình bày.

Sản phẩm phải đủ rõ ràng để:
- đội dev có thể triển khai theo phase;
- AI coding agent có thể dựa vào tài liệu này để sinh code theo module;
- hệ thống có đường nâng cấp từ MVP lên production trên Kubernetes.

---

## 2. Phạm vi

### 2.1 In scope
- Chat UI tương tự ChatGPT.
- Backend FastAPI.
- Agent orchestration bằng **PydanticAI** hoặc **LangGraph**.
- Hỗ trợ nhiều LLM provider: OpenAI, Anthropic, Gemini, Ollama.
- Upload và xử lý tài liệu cho RAG: **PDF, DOCX, XLSX** ở phase đầu; mở rộng **DOC, XLS** ở phase sau bằng conversion pipeline.
- Vector search bằng Qdrant.
- Metadata và nghiệp vụ ứng dụng trong PostgreSQL.
- Cache và queue support bằng Redis.
- Object storage bằng MinIO.
- Ingestion background jobs bằng Celery.
- Observability bằng Langfuse.
- Ontology service bằng Python, Neo4j ở phase graph chính thức.
- MCP Gateway tự xây, có thể kết nối được các loại MCP server phổ biến.
- Giao diện ontology explorer, narrative builder, dashboard HTML builder.
- Docker cho local/dev, Kubernetes cho production.

### 2.2 Out of scope cho giai đoạn đầu
- Tác vụ agent tự động nhiều giờ, scheduler phức tạp.
- Quy trình phê duyệt nhiều cấp cho write-action.
- Hệ thống BI enterprise đầy đủ thay thế Power BI/Tableau.
- Ontology reasoning cấp độ học thuật đầy đủ OWL-DL.
- Real-time collaborative editing đa người trên cùng dashboard.

---

## 3. Mục tiêu nghiệp vụ

### 3.1 Mục tiêu người dùng cuối
- Hỏi đáp nhanh như ChatGPT.
- Nhận câu trả lời có dẫn nguồn tài liệu.
- Có thể truy hồi, xem các khái niệm/thực thể/quan hệ được trích ra từ tài liệu.
- Có thể dựng narrative và dashboard từ ontology mà không cần tự viết Cypher hoặc code.

### 3.2 Mục tiêu cho quản trị tri thức
- Tải tài liệu lên, theo dõi trạng thái parse/index/extract.
- Kiểm soát chất lượng ontology được AI trích xuất.
- Quản lý dictionary, synonym, taxonomy, relation types.
- Theo dõi provenance: một thực thể/quan hệ được tạo từ tài liệu nào, đoạn nào.

### 3.3 Mục tiêu kỹ thuật
- Hệ thống module hóa rõ để dễ scale.
- Mỗi lớp có interface rõ ràng: Chat, Agent, Retrieval, Ontology, MCP, Narrative, Dashboard.
- Có logging, tracing, audit.
- Có cơ chế nâng cấp dần mà không phải phá kiến trúc cũ.

---

## 4. Vai trò người dùng

| Vai trò | Mục đích sử dụng | Quyền chính |
|---|---|---|
| End User | Chat, hỏi đáp, xem nguồn, dùng narrative/dashboard | Chat, upload tài liệu trong phạm vi được cấp, xem ontology đã publish |
| Knowledge Admin | Quản lý tài liệu và pipeline RAG | Upload/bulk upload, reprocess, xem chunk/index status |
| Ontology Admin | Quản lý ontology và graph | Duyệt entity/relation, merge node, sửa synonym, publish ontology version |
| Workspace Admin | Quản lý cấu hình workspace | LLM provider, provider env/endpoint, task-to-model routing, MCP connectors, quyền truy cập |
| System Admin | Vận hành hệ thống | Secret, deployment, observability, backup/restore |
| Developer | Mở rộng hệ thống | API, worker, parser, connector, UI modules |

---

## 5. Kiến trúc mục tiêu

### 5.1 Stack chốt

- **Frontend:** Next.js
- **Backend API:** FastAPI
- **Agent:** PydanticAI hoặc LangGraph
- **LLM Providers:** OpenAI, Anthropic, Gemini, Ollama
- **Vector DB:** Qdrant
- **App DB:** PostgreSQL
- **Cache / Queue infra:** Redis
- **Object Storage:** MinIO
- **Ontology service:** Python service
- **Graph DB:** Neo4j (phase graph chính thức)
- **MCP:** Custom MCP Gateway
- **Background jobs:** Celery
- **Observability:** Langfuse
- **Deploy:** Docker -> Kubernetes

### 5.2 Kiến trúc logic

```text
[Next.js UI]
   |- Chat UI
   |- Ontology Explorer
   |- Narrative Builder
   |- Dashboard Builder
   |- Admin Console

        |
        v

[FastAPI Backend / API Gateway]
   |- Auth / RBAC
   |- Chat API
   |- Document API
   |- Ontology API
   |- Narrative API
   |- Dashboard API
   |- MCP API

        |
        v

[Agent Orchestrator]
   |- Conversation Manager
   |- Model Router
   |- Planner / Executor
   |- Retrieval Router
   |- Tool Router
   |- Citation Composer

   |--------------------|-------------------|------------------|
   v                    v                   v
[Qdrant Service]   [Ontology Service]   [MCP Gateway]
   |                    |                   |
   v                    v                   v
[MinIO + PG]        [Neo4j + PG]       [External MCP Servers]

        |
        v

[Celery Workers]
   |- Parse docs
   |- Chunk docs
   |- Embed docs
   |- Build ontology
   |- Sync graph
   |- Generate narrative
   |- Render dashboard HTML
```

### 5.3 Nguyên tắc kiến trúc
1. UI, API, Agent, Retrieval, Ontology, MCP phải tách module rõ.
2. Không để LLM gọi thẳng external tools mà không qua policy layer.
3. Mọi entity/relation trong ontology phải có **provenance** quay về nguồn gốc.
4. Qdrant và Graph phải được kết nối ở mức metadata, không tách rời hoàn toàn.
5. Các phase sau chỉ mở rộng năng lực, không phá API contract chính của phase trước.

---

## 6. Các phân hệ chính

### 6.1 Chat & Conversation
Phân hệ cho phép:
- tạo phiên chat;
- chọn model/provider;
- tự động nạp model mặc định theo task profile hoặc agent profile của workspace;
- chat streaming;
- upload tài liệu trong chat hoặc chọn tài liệu đã có;
- hiển thị citations;
- hiển thị trace: gọi RAG, gọi ontology, gọi MCP.

### 6.2 Multi-LLM Provider Layer
Phân hệ chuẩn hóa cách gọi model từ:
- OpenAI
- Anthropic
- Gemini
- Ollama

Yêu cầu:
- có interface chung cho chat completion / structured extraction / streaming;
- có cấu hình theo workspace;
- cho phép người dùng nhập/cập nhật provider env hoặc endpoint ở UI/API dành cho workspace admin;
- có model catalog với metadata đủ dùng cho người vận hành:
  - provider;
  - model id;
  - label hiển thị;
  - context window;
  - khả năng streaming;
  - khả năng structured output;
  - readiness status;
  - task recommendations;
- cho phép gán model theo task thay vì chỉ theo chat:
  - chat;
  - retrieval answer synthesis;
  - ontology extraction;
  - narrative generation;
  - dashboard generation;
- phải làm nền cho bước sau là agent builder/profile builder:
  - mỗi agent profile có thể mang task-to-model mapping riêng;
  - có thể gắn prompt/policy/tool scope theo profile ở phase sau;
- có routing policy và fallback policy;
- có logging token usage, latency, error rate.

### 6.2.1 Agent / Model Configuration Layer
Ngoài lớp adapter provider, hệ thống cần một lớp cấu hình để Workspace Admin có thể:
- bật/tắt provider theo workspace;
- nhập secret hoặc endpoint cần thiết cho từng provider;
- xem trạng thái provider/model đang sẵn sàng hay bị block vì thiếu env hoặc thiếu runtime adapter;
- gán model mặc định theo task;
- về sau tạo nhiều agent profile khác nhau dùng chung model catalog nhưng khác task routing, prompt và tool policy.

### 6.3 Document Ingestion & RAG
Phân hệ nhận tài liệu, parse, chunk, embed và index vào Qdrant để phục vụ RAG.

Bắt buộc hỗ trợ:
- PDF
- DOCX
- XLSX

Mở rộng ở phase sau:
- DOC
- XLS
- CSV
- PPTX

### 6.4 Ontology Builder & Graph
Phân hệ AI đọc tài liệu, trích xuất:
- entity
- concept
- relation
- taxonomy/synonym
- provenance

Sau đó ghi vào graph store và cung cấp UI để quản trị.

### 6.5 MCP Gateway
Phân hệ quản lý danh sách MCP server, discover tools, policy, credentials và runtime invocation.

### 6.6 Ontology Explorer UI
Phân hệ hiển thị:
- graph view;
- table view của entity/relation;
- chi tiết thực thể;
- evidence/source;
- review queue;
- version compare.

### 6.7 Narrative Builder
Phân hệ sinh narrative dựa trên ontology/subgraph:
- executive summary;
- domain narrative;
- dependency narrative;
- impact narrative;
- knowledge brief.

### 6.8 Dashboard HTML Builder
Phân hệ sinh dashboard HTML từ ontology:
- cards
- tables
- charts
- dependency map
- summary panels

---

## 7. Luồng dữ liệu cấp cao

### 7.1 Luồng chat với RAG
1. User gửi câu hỏi.
2. Agent router xác định có cần RAG không.
3. Query được rewrite và enrich metadata filter.
4. Retriever lấy top-k chunks từ Qdrant.
5. Nếu có ontology mapping thì đính kèm entity/concept liên quan.
6. Rerank kết quả.
7. LLM tổng hợp câu trả lời.
8. UI hiển thị answer + citations + tool trace.

### 7.2 Luồng build ontology từ tài liệu
1. User upload tài liệu.
2. Document parser chuẩn hóa nội dung theo format.
3. Worker tạo chunks và metadata cấu trúc.
4. Ontology extraction worker chạy entity/relation extraction.
5. Entity resolution so khớp với ontology hiện có.
6. Sinh candidate nodes/edges.
7. Tính confidence score.
8. Auto-approve hoặc đưa vào review queue.
9. Publish vào Neo4j + Postgres metadata.
10. UI ontology hiển thị graph đã cập nhật.

### 7.3 Luồng narrative/dashboard
1. User chọn ontology scope hoặc chọn một subgraph.
2. Backend query graph để lấy dữ liệu.
3. AI sinh outline narrative hoặc đề xuất widget dashboard.
4. Narrative/dashboard được render thành HTML/Markdown.
5. Lưu artifact vào MinIO, metadata vào Postgres.
6. Người dùng xem, chỉnh sửa, publish hoặc export.

### 7.4 Luồng gọi MCP
1. Agent quyết định cần gọi tool.
2. Tool router tra registry và quyền truy cập.
3. MCP Gateway discover/invoke tool.
4. Kết quả được normalize.
5. Agent tổng hợp kết quả cùng RAG/ontology nếu cần.
6. UI hiển thị tool call trace và answer cuối.

---

## 8. Yêu cầu chức năng chi tiết

## 8.1 Chat UI

### 8.1.1 Chức năng chính
- Tạo/xóa/đổi tên phiên chat.
- Chọn model/provider theo từng chat.
- Cho phép chat dùng model mặc định từ task `chat` của workspace hoặc agent profile đang chọn.
- Cho phép override model thủ công ở từng chat nếu workspace policy cho phép.
- Chat streaming.
- Upload file trong chat.
- Đính citations vào câu trả lời.
- Hiển thị trạng thái đang gọi RAG, Ontology, MCP.
- Lưu lịch sử hội thoại.

### 8.1.2 Thành phần UI tối thiểu
- Sidebar conversation list.
- Main chat panel.
- Message composer.
- Model selector.
- Agent/profile selector hoặc task preset selector ở phase có agent builder.
- Source viewer drawer.
- Tool trace drawer.
- Upload modal.
- Workspace selector.

### 8.1.3 API tối thiểu
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{id}`
- `POST /api/v1/chat/sessions/{id}/messages/stream`
- `POST /api/v1/chat/sessions/{id}/attachments`
- `GET /api/v1/chat/messages/{id}/sources`
- `PATCH /api/v1/chat/sessions/{id}/model-selection`

---

## 8.2 Multi-LLM Provider Layer

### 8.2.1 Mục tiêu
Tạo một lớp adapter thống nhất để backend không phụ thuộc vào từng provider.

### 8.2.2 Yêu cầu
- Chuẩn hóa request/response.
- Hỗ trợ streaming.
- Hỗ trợ structured output cho extraction.
- Lưu usage/cost/latency/error.
- Cho phép fallback nếu provider lỗi.
- Cho phép cấu hình model theo use case:
  - chat generation
  - ontology extraction
  - summarization
  - dashboard narrative generation
- Cho phép Workspace Admin nhập env/credential hoặc endpoint cho provider bằng UI/API.
- Không bắt buộc toàn bộ provider phải lấy từ env file của hệ thống; cần hỗ trợ cấu hình ở mức workspace metadata hoặc secret store.
- Mỗi model trong catalog phải có metadata tối thiểu:
  - `provider`
  - `model`
  - `label`
  - `description`
  - `context_window`
  - `supports_streaming`
  - `supports_structured_output`
  - `supports_runtime`
  - `required_env_fields`
  - `missing_env_fields`
  - `recommended_for_tasks`
- Phải có readiness reason rõ ràng, ví dụ:
  - thiếu API key;
  - provider bị disable;
  - runtime adapter chưa implement;
  - model bị policy chặn.

### 8.2.2.a Task-based model routing
Hệ thống phải hỗ trợ mapping model theo task ở mức workspace.

Task tối thiểu:
- `chat`
- `retrieval`
- `ontology_extraction`
- `narrative_generation`
- `dashboard_generation`

Mỗi task assignment cần lưu tối thiểu:
- `workspace_id`
- `task_type`
- `provider`
- `model`
- `fallback_provider` hoặc `fallback_chain` ở phase sau
- `updated_by`
- `updated_at`

### 8.2.2.b Agent builder foundation
Từ phase đầu của lớp Multi-LLM, thiết kế phải chừa chỗ cho `agent profiles`.

Một agent profile ở phase sau có thể bao gồm:
- `agent_profile_id`
- `name`
- `description`
- `system_prompt`
- `task_model_mapping`
- `tool_policy_scope`
- `visibility`
- `status`

Ở giai đoạn hiện tại chưa bắt buộc làm đầy đủ UI tạo agent profile, nhưng API/data model không được chặn khả năng mở rộng này.

### 8.2.3 Chính sách routing đề xuất
- Chat thường: model mặc định theo workspace.
- Trích xuất ontology: model ưu tiên structured output ổn định.
- Tài liệu nhạy cảm/private: cho phép route sang Ollama nội bộ.
- Fallback: OpenAI -> Anthropic -> Gemini hoặc policy do admin cấu hình.

### 8.2.4 API tối thiểu
- `GET /api/v1/models/providers`
- `GET /api/v1/models`
- `POST /api/v1/admin/models/config`
- `POST /api/v1/admin/models/test`
- `GET /api/v1/agents/settings`
- `PUT /api/v1/agents/settings`
- `GET /api/v1/agents/tasks`
- `GET /api/v1/agents/catalog`

---

## 8.3 Document Ingestion & Qdrant RAG

### 8.3.1 Phạm vi file support
**Bắt buộc phase đầu:**
- `.pdf`
- `.docx`
- `.xlsx`

**Khuyến nghị phase sau:**
- `.doc`
- `.xls`
- `.csv`
- `.pptx`

### 8.3.2 Yêu cầu xử lý từng loại tài liệu

#### PDF
Phải xử lý được:
- text layer;
- heading nếu suy ra được;
- page number;
- table blocks cơ bản;
- citations theo page;
- OCR fallback cho scanned PDF ở phase nâng cao.

Metadata tối thiểu:
- `document_id`
- `page_number`
- `section_title`
- `chunk_index`
- `source_path`
- `workspace_id`

#### DOCX
Phải giữ được:
- heading hierarchy;
- paragraph groups;
- list items;
- tables;
- section titles;
- citations theo heading/section.

Metadata tối thiểu:
- `document_id`
- `heading_path`
- `table_index`
- `chunk_index`
- `source_path`
- `workspace_id`

#### XLSX
Phải xử lý được:
- nhiều sheet;
- header row detection;
- table range detection;
- merged cells ở mức chấp nhận được;
- row-group chunking;
- citations theo sheet + row range.

Metadata tối thiểu:
- `document_id`
- `sheet_name`
- `table_name` hoặc `detected_table_id`
- `row_start`
- `row_end`
- `column_headers`
- `chunk_index`
- `workspace_id`

### 8.3.3 Chiến lược chunking

#### Với PDF/DOCX
Ưu tiên chunk theo cấu trúc:
1. heading -> section -> paragraph group;
2. giới hạn token theo model embedding;
3. giữ overlap giữa các chunk kế cận;
4. chunk phải đủ context nhưng không quá dài.

#### Với XLSX
Không chunk như văn bản thuần.
Phải có 2 lớp chunk:
1. **Schema chunk**: mô tả sheet, cột, ý nghĩa bảng.
2. **Data row group chunk**: nhóm các dòng liên quan thành đoạn mô tả text có cấu trúc.

Ví dụ row-group text:
- Sheet: Sales
- Columns: Month, Region, Revenue, Product
- Rows 10-25
- Summary text synthesized for embedding

### 8.3.4 Dữ liệu lưu ở đâu
- File gốc: MinIO
- Metadata tài liệu và job: PostgreSQL
- Vector/chunk payload: Qdrant
- Optional parsed JSON trung gian: MinIO/Postgres tùy dung lượng

### 8.3.5 Qdrant collection design
Tối thiểu cần 1 collection chunks với payload:
- `chunk_id`
- `document_id`
- `workspace_id`
- `document_type`
- `page_number`
- `sheet_name`
- `row_start`
- `row_end`
- `heading_path`
- `text`
- `source_url`
- `ontology_entity_ids` (nếu có)
- `created_at`

Khuyến nghị thêm:
- `document_tags`
- `security_labels`
- `language`
- `parser_version`
- `embedding_model`
- `version`

### 8.3.6 Retrieval pipeline
1. Normalize query.
2. Query rewrite.
3. Expand bằng synonym/taxonomy từ ontology nếu có.
4. Apply metadata filter theo workspace/document/tag.
5. Search Qdrant.
6. Rerank top-k.
7. Compose citations.
8. Trả về context cho LLM.

### 8.3.7 API tối thiểu
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/jobs`
- `POST /api/v1/documents/{id}/reprocess`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/retrieval/reindex`

---

## 8.4 Build Ontology bằng AI từ tài liệu

Đây là phân hệ quan trọng, phải đủ chi tiết để triển khai thành pipeline thật.

### 8.4.1 Mục tiêu
Tự động đọc tài liệu người dùng tải lên và sinh ra:
- entity;
- concept;
- relation;
- synonym;
- taxonomy candidates;
- provenance;
- graph updates.

Hệ thống không chỉ “trích entity” mà còn phải:
- so khớp với graph hiện có;
- tránh tạo node trùng;
- lưu bằng chứng và confidence;
- hỗ trợ review/publish.

### 8.4.2 Kết quả đầu ra bắt buộc
Mỗi lần build ontology từ tài liệu phải tạo ra các artifact sau:
1. `document_parse_result`
2. `ontology_extraction_result`
3. `candidate_entities`
4. `candidate_relations`
5. `entity_resolution_result`
6. `graph_upsert_plan`
7. `review_queue_items`
8. `published_graph_delta` (nếu được approve)

### 8.4.3 Kiến trúc pipeline
Pipeline nên tách thành các bước độc lập, mỗi bước có thể chạy job riêng.

#### Bước 1: Document normalization
- Nhận parsed content từ ingestion pipeline.
- Chuẩn hóa về một format trung gian thống nhất, ví dụ:
  - `document`
  - `sections`
  - `tables`
  - `rows`
  - `chunks`
  - `metadata`

Đầu ra:
```json
{
  "document_id": "...",
  "title": "...",
  "document_type": "pdf|docx|xlsx",
  "sections": [],
  "tables": [],
  "chunks": [],
  "metadata": {}
}
```

#### Bước 2: Domain classification
AI hoặc rule-based classifier xác định tài liệu thuộc domain nào:
- policy
- process
- org
- product
- dataset
- contract
- report
- operations
- finance
- HR
- engineering
- customer

Kết quả dùng để:
- chọn ontology extraction prompt;
- chọn entity types ưu tiên;
- áp dụng taxonomy phù hợp.

#### Bước 3: Candidate entity extraction
Kết hợp 3 lớp:
1. **Rule-based extraction**  
   Regex / heuristic cho email, URL, ID, code, số liệu, ngày tháng, version, tên bảng, header cột.
2. **LLM structured extraction**  
   LLM trả về JSON entity candidates theo schema.
3. **Dictionary / ontology lookup**  
   So khớp với glossary, taxonomy, synonym list hiện có.

Output mỗi entity candidate tối thiểu:
- `candidate_id`
- `label`
- `entity_type`
- `aliases`
- `description`
- `source_document_id`
- `source_chunk_id`
- `evidence_text`
- `confidence`
- `domain`

#### Bước 4: Candidate relation extraction
Trích quan hệ từ:
- câu văn;
- heading hierarchy;
- bảng;
- sheet-column semantics;
- document metadata.

Output mỗi relation candidate tối thiểu:
- `from_entity_candidate_id`
- `to_entity_candidate_id`
- `relation_type`
- `direction`
- `evidence_text`
- `source_document_id`
- `source_chunk_id`
- `confidence`

#### Bước 5: Entity resolution / canonicalization
Đây là bước bắt buộc để tránh graph rác.

So khớp entity candidate với entity hiện có theo thứ tự:
1. exact match theo canonical name;
2. match theo alias/synonym;
3. fuzzy match;
4. vector similarity trên label + description;
5. context similarity theo neighboring relations.

Kết quả có 3 khả năng:
- `MERGE_TO_EXISTING`
- `CREATE_NEW_ENTITY`
- `REVIEW_REQUIRED`

Entity resolution output:
- `candidate_id`
- `decision`
- `matched_entity_id`
- `match_score`
- `reason`

#### Bước 6: Taxonomy / synonym expansion
Nếu candidate là concept mới hoặc alias mới:
- thêm vào dictionary;
- gắn `SAME_AS`, `ALIAS_OF`, `INSTANCE_OF`, `PART_OF`;
- đề xuất node taxonomy nếu phù hợp.

#### Bước 7: Confidence scoring
Confidence không nên chỉ lấy từ LLM.
Nên tính theo công thức tổ hợp:
- điểm extractor;
- điểm rule-based;
- số lượng evidence độc lập;
- mức match với ontology hiện có;
- độ nhất quán giữa các chunk;
- loại tài liệu.

Gợi ý ngưỡng:
- `>= 0.90`: auto-approve cho node/edge ít rủi ro.
- `0.70 - 0.89`: đưa review queue.
- `< 0.70`: giữ ở draft, chưa publish.

#### Bước 8: Review queue
Review queue cho Ontology Admin:
- xem candidate;
- xem evidence gốc;
- merge vào node cũ;
- sửa type;
- sửa relation;
- approve / reject.

#### Bước 9: Graph upsert
Sau khi approve:
- tạo hoặc update node/edge trong Neo4j;
- lưu provenance;
- tạo version delta;
- cập nhật link ngược về tài liệu/chunk.

#### Bước 10: Publish ontology version
Mỗi đợt publish phải có:
- version number;
- summary of changes;
- created_by;
- created_at;
- delta count.

### 8.4.4 Mô hình graph đề xuất

#### Node types tối thiểu phase đầu
- `Document`
- `Chunk`
- `Concept`
- `Entity`
- `Person`
- `Organization`
- `Team`
- `Role`
- `System`
- `Product`
- `Process`
- `Policy`
- `Metric`
- `Dataset`
- `Report`
- `Location`
- `CustomerSegment`
- `Tag`

#### Relation types tối thiểu phase đầu
- `MENTIONS`
- `DEFINED_IN`
- `INSTANCE_OF`
- `PART_OF`
- `BELONGS_TO`
- `OWNED_BY`
- `USED_BY`
- `DEPENDS_ON`
- `RELATES_TO`
- `APPLIES_TO`
- `TRACKED_BY`
- `GENERATED_FROM`
- `ALIAS_OF`
- `SAME_AS`
- `CITES`
- `LOCATED_IN`

#### Provenance relations bắt buộc
- `EXTRACTED_FROM` giữa entity/relation và chunk/document
- `SUPPORTED_BY` tới evidence node hoặc metadata record

### 8.4.5 Lưu provenance
Mọi node/edge do AI sinh ra phải truy ngược được:
- tài liệu nào sinh ra;
- đoạn nào sinh ra;
- model nào dùng để sinh;
- version parser/extractor;
- confidence;
- người nào approve.

Nếu thiếu provenance, item không được publish.

### 8.4.6 Prompt strategy cho ontology extraction
Nên có prompt theo domain, không dùng 1 prompt duy nhất cho mọi tài liệu.

Ví dụ nhóm prompt:
- policy extraction
- process extraction
- org structure extraction
- metrics extraction
- product/system extraction
- spreadsheet semantic extraction

Structured output schema phải cố định để AI agent code được parser.

### 8.4.7 Đặc thù extraction từ Excel
Excel không chỉ là “text trong sheet”.
Phải khai thác:
- tên sheet;
- cột;
- row group;
- công thức nếu cần;
- units;
- KPI/Metric;
- dimension fields.

Ví dụ từ sheet KPI:
- `Revenue` có thể là `Metric`
- `Region` là dimension
- `Product Line` là dimension hoặc entity
- quan hệ `Metric APPLIES_TO Region`

Ngoài extraction bằng LLM, phải có lớp rule-based:
- numeric column detector;
- categorical column detector;
- date/time column detector;
- metric name detector.

### 8.4.8 Đặc thù extraction từ PDF/DOCX
Phải tận dụng:
- heading hierarchy;
- glossary sections;
- definitions;
- tables;
- appendices.

Ví dụ:
- Mục “Definitions” rất dễ sinh `Concept`
- Mục “Roles & Responsibilities” dễ sinh `Role`, `Team`, `OWNED_BY`
- Mục “KPI” dễ sinh `Metric`, `TRACKED_BY`

### 8.4.9 Chế độ vận hành ontology
Hệ thống cần 3 trạng thái ontology item:
- `draft`
- `reviewed`
- `published`

Không publish trực tiếp toàn bộ mọi thứ AI trích ra.

### 8.4.10 API tối thiểu
- `POST /api/v1/ontology/build/{document_id}`
- `GET /api/v1/ontology/jobs/{job_id}`
- `GET /api/v1/ontology/candidates`
- `POST /api/v1/ontology/candidates/{id}/approve`
- `POST /api/v1/ontology/candidates/{id}/reject`
- `POST /api/v1/ontology/candidates/{id}/merge`
- `GET /api/v1/ontology/entities`
- `GET /api/v1/ontology/entities/{id}`
- `GET /api/v1/ontology/relations`
- `GET /api/v1/ontology/subgraph`
- `POST /api/v1/ontology/publish`

---

## 8.5 MCP Gateway

### 8.5.1 Mục tiêu
Tạo custom gateway có thể kết nối nhiều loại MCP server và expose tools cho agent một cách thống nhất.

### 8.5.2 Yêu cầu
- Registry của MCP server theo workspace.
- Lưu cấu hình connection và secret an toàn.
- Support các mode kết nối phổ biến:
  - local/stdin-stdio;
  - remote/http;
  - remote/sse nếu có.
- Discover tools.
- Cache tool schema.
- Policy theo tool:
  - read-only
  - write-with-confirmation
  - admin-only
- Timeout, retry, logging, audit.

### 8.5.3 Chuẩn dữ liệu tool trong hệ thống
Mỗi tool sau khi discover phải được normalize thành:
- `tool_id`
- `server_id`
- `name`
- `description`
- `input_schema`
- `output_schema`
- `capabilities`
- `risk_level`
- `workspace_id`

### 8.5.4 Runtime invocation
Luồng invoke:
1. agent yêu cầu tool;
2. backend check quyền;
3. gateway invoke;
4. normalize output;
5. trả về agent.

### 8.5.5 API tối thiểu
- `POST /api/v1/mcp/servers`
- `GET /api/v1/mcp/servers`
- `POST /api/v1/mcp/servers/{id}/discover`
- `GET /api/v1/mcp/tools`
- `POST /api/v1/mcp/tools/{id}/invoke`
- `POST /api/v1/mcp/tools/{id}/test`
- `POST /api/v1/mcp/servers/{id}/rotate-secret`

---

## 8.6 Ontology Explorer UI

### 8.6.1 Mục tiêu
Cho phép người dùng duyệt ontology theo dạng trực quan và có thể review graph.

### 8.6.2 Màn hình tối thiểu
1. **Graph Canvas**
   - zoom/pan
   - expand neighbors
   - filter theo type
   - highlight path
2. **Entity List**
   - search
   - filter
   - sort theo type/confidence/updated time
3. **Entity Detail Drawer**
   - node properties
   - aliases
   - related entities
   - evidence
   - source documents
4. **Review Queue**
   - candidate entity/relation
   - approve/reject/merge
5. **Version Compare**
   - so sánh ontology version theo delta

### 8.6.3 Data nguồn
- Graph data từ Neo4j
- Metadata, review status từ Postgres
- Evidence links từ MinIO/Postgres

---

## 8.7 Narrative Builder

### 8.7.1 Mục tiêu
Sinh nội dung narrative từ ontology/subgraph phục vụ báo cáo, giải thích hoặc tóm tắt.

### 8.7.2 Các loại narrative tối thiểu
- Executive summary
- Domain overview
- Dependency story
- Impact analysis
- Risk summary
- Process narrative

### 8.7.3 Cơ chế hoạt động
1. User chọn scope:
   - workspace;
   - ontology node;
   - subgraph;
   - filter theo tag/type/time.
2. System query graph.
3. AI tạo outline.
4. AI sinh narrative có dẫn nguồn:
   - entity references
   - relation evidence
   - source docs
5. User chỉnh sửa và publish/export.

### 8.7.4 Output format
- Markdown
- HTML
- JSON cấu trúc để dùng lại
- Optional PDF ở phase sau

### 8.7.5 API tối thiểu
- `POST /api/v1/narratives/generate`
- `GET /api/v1/narratives`
- `GET /api/v1/narratives/{id}`
- `POST /api/v1/narratives/{id}/publish`
- `POST /api/v1/narratives/{id}/export`

---

## 8.8 Dashboard HTML Builder

### 8.8.1 Mục tiêu
Sinh dashboard HTML từ ontology mà không cần tự viết code frontend.

### 8.8.2 Phạm vi
Dashboard được sinh từ:
- graph query result;
- ontology aggregates;
- saved narratives;
- selected subgraph.

### 8.8.3 Widget tối thiểu
- KPI Card
- Summary Table
- Entity Distribution Chart
- Relationship Count Chart
- Timeline (nếu có time data)
- Dependency Map
- Evidence List

### 8.8.4 Luồng tạo dashboard
1. User chọn ontology scope hoặc saved query.
2. System gợi ý widget.
3. User chọn layout/template.
4. Backend sinh config JSON.
5. Renderer tạo HTML bundle.
6. Lưu artifact lên MinIO.
7. User xem trước, publish, chia sẻ nội bộ.

### 8.8.5 Yêu cầu
- Dashboard phải có link về ontology nodes/source docs.
- HTML phải độc lập đủ để render lại.
- Layout responsive cơ bản.
- Có versioning.

### 8.8.6 API tối thiểu
- `POST /api/v1/dashboards/generate`
- `GET /api/v1/dashboards`
- `GET /api/v1/dashboards/{id}`
- `POST /api/v1/dashboards/{id}/publish`
- `GET /api/v1/dashboards/{id}/artifact`

---

## 9. Mô hình dữ liệu mức cao

## 9.1 PostgreSQL tables gợi ý

### Core application
- `users`
- `workspaces`
- `workspace_members`
- `roles`
- `permissions`

### Chat
- `chat_sessions`
- `chat_messages`
- `chat_attachments`
- `model_configs`
- `model_usage_logs`
- `provider_configs`
- `task_model_configs`
- `agent_profiles` (phase sau hoặc tạo skeleton từ sớm)
- `agent_profile_task_models` (phase sau)

### Documents
- `documents`
- `document_versions`
- `document_jobs`
- `parsed_documents`
- `chunk_metadata`

### Ontology
- `ontology_candidates`
- `ontology_candidate_evidence`
- `ontology_review_actions`
- `ontology_versions`
- `ontology_publish_logs`
- `entity_aliases`
- `taxonomy_terms`

### MCP
- `mcp_servers`
- `mcp_tools`
- `mcp_tool_invocations`
- `mcp_credentials_refs`

### Narrative / Dashboard
- `narratives`
- `narrative_versions`
- `dashboards`
- `dashboard_versions`
- `artifacts`

### System / Audit
- `audit_logs`
- `job_runs`
- `feature_flags`
- `workspace_settings`

## 9.2 Qdrant collection
- `document_chunks`

## 9.3 Neo4j graph
Node labels và relationship types như mục Ontology đã nêu.

---

## 10. Yêu cầu phi chức năng

### 10.1 Bảo mật
- Auth và RBAC theo workspace.
- Secret của LLM/MCP lưu an toàn.
- Không để tool write-action chạy không qua policy.
- Provenance và audit bắt buộc.

### 10.2 Hiệu năng
- Chat streaming bắt đầu trong thời gian chấp nhận được.
- Search Qdrant top-k trong thời gian chấp nhận được cho tài liệu cỡ trung bình.
- Narrative và dashboard là async job nếu nặng.

### 10.3 Vận hành
- Có log và trace cho từng request/job.
- Có retry policy cho worker.
- Có dead-letter/failure handling tối thiểu.
- Có backup cho Postgres, Neo4j, MinIO.

### 10.4 Mở rộng
- Thêm provider/model không đổi core logic.
- Thêm parser file mới không đổi chat API.
- Thêm MCP server không đổi agent core.
- Có thể nâng từ single instance lên Kubernetes.

---

## 11. Chia phase triển khai

Dưới đây là roadmap đề xuất. Mỗi phase phải kết thúc bằng một trạng thái deployable và có thể demo được.

| Phase | Tên phase | Kết quả chốt |
|---|---|---|
| Phase 0 | Foundation & Project Skeleton | Chạy được hệ thống khung, auth cơ bản, DB/storage/cache, observability, CI/CD local |
| Phase 1 | Chat Core & Multi-LLM | Có chat UI, lưu hội thoại, streaming, chọn model/provider, có provider env config và task-based model routing foundation |
| Phase 2 | Document Ingestion & Qdrant RAG | Upload PDF/DOCX/XLSX, parse/chunk/embed/index, hỏi đáp có citations |
| Phase 3 | Ontology AI Extraction & Graph Foundation | Tự build entity/relation từ tài liệu, review queue, sync graph |
| Phase 4 | MCP Gateway & Agent Tooling | Kết nối MCP server, discover/invoke tools, agent dùng tool có policy, bắt đầu có agent profile thực dụng |
| Phase 5 | Ontology Explorer + Narrative + Dashboard HTML | Có UI xem ontology, generate narrative, generate dashboard HTML |
| Phase 6 | Hardening, Evaluation, K8s Production | RBAC đầy đủ, audit, backup, benchmark, deploy Kubernetes |

---

## 12. Chi tiết từng phase

## Phase 0 - Foundation & Project Skeleton

### Mục tiêu
Tạo nền kỹ thuật đủ chắc để các phase sau chỉ việc cắm module.

### Phạm vi
- Monorepo hoặc repo structure rõ ràng.
- Docker Compose cho local dev.
- FastAPI app skeleton.
- Next.js app skeleton.
- PostgreSQL, Redis, MinIO local.
- Langfuse tích hợp cơ bản.
- Auth skeleton, workspace skeleton.
- Celery worker skeleton.
- Common config management.

### Deliverables
- Repo chạy local bằng 1 lệnh compose.
- API healthcheck.
- UI shell có login placeholder.
- DB migrations.
- MinIO bucket setup.
- Redis + Celery worker up.
- Langfuse trace được request mẫu.

### API/UI tối thiểu
- `/health`
- `/api/v1/auth/me`
- shell UI: login, workspace selector placeholder

### Definition of Done
- Dev mới clone repo và chạy được local.
- Có seed data workspace/user demo.
- Có CI lint/test/build cơ bản.
- Có env strategy rõ ràng cho dev/staging/prod.

---

## Phase 1 - Chat Core & Multi-LLM

### Mục tiêu
Cho người dùng chat được như ChatGPT và chọn model từ OpenAI/Anthropic/Gemini/Ollama.

### Phạm vi
- Conversation sessions.
- Message history.
- Streaming responses.
- Model/provider selector.
- Provider env / endpoint configuration cho Workspace Admin.
- Model catalog kèm readiness status và metadata.
- Task-based model routing foundation.
- Unified LLM adapter.
- Token/cost logging.
- Model fallback policy mức cơ bản.

### Deliverables
- Chat UI usable.
- Tạo chat mới, đổi tên, xem lịch sử.
- Chọn provider/model.
- Có màn hình cấu hình provider env và task-to-model mapping.
- Có API để đọc/ghi agent settings ở mức workspace.
- Streaming trả lời.
- Log usage theo message.

### Backend modules cần có
- `llm_provider_adapter`
- `conversation_service`
- `chat_stream_service`
- `model_config_service`
- `provider_config_service` hoặc gộp trong `model_config_service`
- `task_routing_service` hoặc gộp trong `model_config_service`

### Definition of Done
- 1 workspace có thể cấu hình ít nhất 4 provider.
- Workspace Admin có thể nhập/cập nhật credential hoặc endpoint cho provider mà không cần sửa file `.env` trực tiếp trên server.
- UI hiển thị được model catalog với trạng thái `ready/not ready` và lý do.
- Có thể gán model khác nhau cho các task tối thiểu: chat, retrieval, ontology extraction, narrative, dashboard.
- User chọn model khác nhau cho từng chat.
- Nếu provider A lỗi, fallback theo policy.
- Toàn bộ chat lưu vào Postgres.
- Traces xuất hiện trong Langfuse.

---

## Phase 2 - Document Ingestion & Qdrant RAG

### Mục tiêu
Hệ thống nhận tài liệu và trả lời được câu hỏi có dẫn nguồn.

### Phạm vi
- Upload file.
- Parse PDF/DOCX/XLSX.
- Chunking theo format.
- Embedding.
- Index vào Qdrant.
- Retrieval API.
- Chat + RAG integration.
- Citations UI.
- Document admin page.

### Deliverables
- User upload file từ chat hoặc document screen.
- Hệ thống parse được PDF/DOCX/XLSX.
- Qdrant có vectors.
- Search top-k hoạt động.
- Chat trả lời có citations:
  - PDF: page
  - DOCX: heading/section
  - XLSX: sheet + row range
- Admin xem trạng thái job.

### Worker jobs cần có
- `parse_document`
- `build_chunks`
- `embed_chunks`
- `upsert_qdrant`
- `reindex_document`

### Definition of Done
- File upload xong có trạng thái từ `uploaded` -> `parsed` -> `indexed`.
- Ít nhất 1 câu hỏi trên mỗi loại file trả về answer có citations đúng loại.
- User có thể reprocess tài liệu.
- Chunk metadata xem lại được.
- Search API hỗ trợ filter theo workspace/document/tag.

### Lưu ý implementation bắt buộc
- PDF/DOCX không được chunk mù theo số ký tự.
- XLSX phải có sheet-aware chunking.
- Parser version phải lưu trong metadata.
- Qdrant payload phải đủ thông tin để render citations.

---

## Phase 3 - Ontology AI Extraction & Graph Foundation

### Mục tiêu
Tự động xây ontology/graph từ tài liệu đã ingest, có review queue và publish flow.

### Phạm vi
- Ontology extraction pipeline.
- Domain classification.
- Entity extraction.
- Relation extraction.
- Entity resolution/canonicalization.
- Review queue.
- Neo4j sync.
- Provenance storage.
- Minimal ontology read API.

### Deliverables
- User chọn tài liệu và chạy build ontology.
- Hệ thống tạo candidate entities/relations.
- Admin review/approve/reject/merge.
- Sau approve, graph được ghi vào Neo4j.
- Có thể query subgraph cơ bản.
- Entity detail có evidence.

### Worker jobs cần có
- `classify_document_domain`
- `extract_entities`
- `extract_relations`
- `resolve_entities`
- `build_graph_upsert_plan`
- `sync_neo4j`
- `publish_ontology_version`

### Definition of Done
- Từ 1 tài liệu PDF/DOCX/XLSX hệ thống sinh ra candidate graph.
- Ít nhất 80% candidate có evidence click ngược về source.
- Admin merge được entity trùng.
- Graph sau publish query được qua API.
- Có version delta của ontology.

### Yêu cầu chi tiết cần chốt trong phase này
- Schema node/edge v1.
- Confidence scoring strategy v1.
- Review UI v1.
- Provenance model v1.
- Prompt templates theo domain v1.

---

## Phase 4 - MCP Gateway & Agent Tooling

### Mục tiêu
Cho agent gọi được tools qua MCP theo cơ chế chuẩn hóa và có kiểm soát.

### Phạm vi
- MCP server registry.
- Tool discovery.
- Tool schema caching.
- Tool invocation runtime.
- Policy/risk level.
- Agent tool router.
- Trace tool call trên UI.

### Deliverables
- Admin thêm MCP server.
- System discover tool list.
- Agent gọi tool read-only.
- Tool output normalize về format chung.
- Chat trace hiển thị tool đã dùng.

### Definition of Done
- Support ít nhất 1 local MCP server và 1 remote MCP server.
- Tool invocation có timeout/retry/log.
- User không có quyền sẽ không gọi được tool restricted.
- Kết quả tool gắn vào answer cuối.
- Tool usage có audit log.

### Ghi chú
Write-action nên chỉ bật ở phase sau hoặc phải có confirmation flow đơn giản.

---

## Phase 5 - Ontology Explorer + Narrative + Dashboard HTML

### Mục tiêu
Biến graph thành giao diện tri thức có thể xem, kể chuyện và dựng dashboard.

### Phạm vi
- Ontology explorer full UI.
- Entity detail / relations / filters.
- Saved graph queries hoặc query builder đơn giản.
- Narrative generation.
- Dashboard config generation.
- HTML dashboard renderer.
- Artifact storage và publish.

### Deliverables
- User xem graph theo node/edge.
- User search/filter entity.
- User chọn subgraph và generate narrative.
- User chọn scope và generate dashboard HTML.
- Artifact narrative/dashboard lưu version.
- Có link ngược về source docs và ontology nodes.

### Definition of Done
- Có ít nhất 3 loại narrative template usable.
- Có ít nhất 5 widget dashboard usable.
- User export HTML hoặc share link nội bộ.
- Narrative và dashboard đều truy được về ontology/source.
- UI đủ dùng cho analyst hoặc admin không biết Cypher.

---

## Phase 6 - Hardening, Evaluation, Kubernetes Production

### Mục tiêu
Đưa hệ thống từ bản làm được sang bản chạy ổn định production.

### Phạm vi
- RBAC đầy đủ.
- Rate limit.
- Backup/restore.
- Security review.
- Evaluation pipeline cho RAG/ontology/tooling.
- Langfuse dashboards.
- Docker image hardening.
- Helm/K8s manifests.
- Autoscaling strategy.
- Disaster recovery tối thiểu.

### Deliverables
- Staging/prod deployment standard.
- Monitoring, alerts, traces.
- Evaluation reports định kỳ.
- Backup scripts/runbooks.
- K8s deployment.
- SLO và operational docs.

### Definition of Done
- Có staging và production.
- Có rollback playbook.
- Có benchmark cho chat, ingestion, retrieval, ontology extraction.
- Có backup restore test thành công.
- Có least-privilege secrets/config strategy.

---

## 13. Đề xuất backlog kỹ thuật theo module

## 13.1 Frontend Next.js
- Chat pages
- Document pages
- Ontology pages
- Narrative pages
- Dashboard pages
- Admin pages
- Shared components
- Trace drawer
- Source viewer
- Graph canvas
- Artifact viewer

## 13.2 Backend FastAPI
- auth module
- workspace module
- chat module
- model provider module
- document module
- retrieval module
- ontology module
- mcp module
- narrative module
- dashboard module
- audit module

## 13.3 Workers
- parser worker
- embedding worker
- ontology worker
- graph sync worker
- narrative worker
- dashboard renderer worker

## 13.4 Infra
- Postgres
- Redis
- MinIO
- Qdrant
- Neo4j
- Langfuse
- Celery Beat (nếu cần)
- Docker/K8s manifests

---

## 14. Gợi ý repo structure

```text
/apps
  /backend
  /frontend
  /frontend-nextjs
  /worker-celery

/packages
  /agent-core
  /llm-adapters
  /retrieval-core
  /ontology-core
  /mcp-gateway
  /narrative-core
  /dashboard-renderer
  /shared-schemas
  /shared-utils

/infrastructure
  /docker
  /k8s
  /helm
  /scripts

/docs
  /architecture
  /api
  /runbooks
```

---

## 15. Tiêu chí nghiệm thu tổng thể

Hệ thống được coi là đạt bản đầu khi:
1. Người dùng chat được với nhiều provider.
2. Upload PDF/DOCX/XLSX và hỏi đáp có citations đúng.
3. Tài liệu upload có thể sinh ontology candidates.
4. Ontology admin review và publish được graph vào Neo4j.
5. Agent gọi được MCP tools qua gateway.
6. Có UI xem ontology.
7. Có thể generate narrative và dashboard HTML từ ontology.
8. Có tracing, logging, artifact storage và versioning.

---

## 16. Rủi ro và lưu ý triển khai

### 16.1 Rủi ro dữ liệu
- PDF scan có thể khó parse -> cần OCR fallback phase sau.
- Excel phức tạp nhiều merge/formula -> cần chiến lược parser dần dần.
- Tài liệu không chuẩn sẽ làm ontology extraction nhiễu.

### 16.2 Rủi ro ontology
- Sinh quá nhiều node trùng nếu canonicalization yếu.
- Graph rác nếu auto-approve quá rộng.
- Cần review queue từ sớm, không để AI ghi thẳng toàn bộ vào graph.

### 16.3 Rủi ro MCP
- Tool schema khác nhau, chất lượng không đồng đều.
- Tool write-action có rủi ro cao.
- Phải có timeout, permission, audit.

### 16.4 Rủi ro UX
- Nếu trace quá ồn sẽ làm chat rối.
- Nếu citations không rõ người dùng sẽ mất niềm tin.
- Nếu ontology UI khó dùng thì narrative/dashboard sẽ ít được khai thác.

---

## 17. Khuyến nghị triển khai thực tế

1. Chốt Phase 0 -> 2 trước để có xương sống: chat + RAG.
2. Ontology phase triển khai ngay sau khi parser/chunking ổn định.
3. Không build graph UI quá sớm trước khi có review flow.
4. MCP nên đưa vào sau khi agent orchestration và permission model đã rõ.
5. Narrative/dashboard chỉ nên build khi ontology query ổn định.

---

## 18. Quyết định chốt cho bản v1

- **Chuẩn file bắt buộc:** PDF, DOCX, XLSX.
- **GraphDB chính thức:** Neo4j từ phase ontology.
- **Storage:** MinIO cho file và artifact.
- **Queue:** Celery + Redis.
- **Tracing:** Langfuse.
- **Deploy progression:** Docker local -> K8s staging/prod.
- **Ontology build policy:** AI extraction + review queue + publish flow.
- **Dashboard output:** HTML artifact versioned.
- **Narrative output:** Markdown + HTML.

---

## 19. Bước tiếp theo sau tài liệu này

Sau khi chốt tài liệu này, cần viết tiếp 4 tài liệu con:
1. API Spec chi tiết từng module.
2. DB Schema chi tiết Postgres + Neo4j.
3. Prompt/Structured schema cho ontology extraction.
4. UI flow/wireframe cho chat, ontology, narrative, dashboard.

Tài liệu hiện tại đủ để:
- chia epic/story/task;
- giao cho AI agent sinh skeleton code;
- bắt đầu Phase 0 ngay.
