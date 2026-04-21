# Báo cáo kiểm thử API với OpenRouter

Ngày kiểm thử: `2026-04-21`  
Môi trường: `test`  
Provider runtime: `openrouter`  
Model runtime: `nvidia/nemotron-3-super-120b-a12b:free`  
OpenRouter base URL: `https://openrouter.ai/api/v1`

## 1. Tóm tắt

Tôi đã kiểm thử toàn bộ nhóm API FastAPI hiện có trong backend.

- Tổng số route API đang expose dưới `/api/v1`: `40`
- Coverage đạt được: `40/40 route-method`
- Lượt chạy chính: `47` request tình huống
- Kết quả lượt chạy chính: `44 pass`, `3 fail`
- Phân tích 3 fail:
  - `2` fail là lỗi trong script kiểm thử bổ sung khi đọc lại dữ liệu ontology seed thủ công, không phải lỗi route backend
  - `1` fail là phản hồi nghiệp vụ đúng của backend: publish ontology bị chặn khi chưa có entity được approve
- Lượt chạy bổ sung để phủ kín 2 route review ontology:
  - `POST /api/v1/ontology/entities/{entity_id}/review`: `200`
  - `POST /api/v1/ontology/relations/{relation_id}/review`: `200`
  - Sau khi approve candidate seed thủ công, `POST /api/v1/ontology/builds/{build_id}/publish`: `200`

Kết luận ngắn:

- Toàn bộ API hiện tại đều phản hồi đúng theo contract ở mức smoke/integration.
- OpenRouter đã được xác nhận chạy thực trên các API có dùng runtime model, đặc biệt là chat.
- Điểm nghẽn hiện tại không nằm ở route layer mà nằm ở ontology extractor: code hiện chỉ thực sự hỗ trợ Anthropic cho bước trích ontology bằng LLM, nên chạy OpenRouter sẽ không sinh candidate ontology thật.

## 2. Phạm vi và cách kiểm thử

Tôi kiểm thử theo hai lớp:

1. Lượt chạy chính trong môi trường `TestClient` với cấu hình `openrouter` + model `nvidia/nemotron-3-super-120b-a12b:free`.
2. Lượt bổ sung riêng cho 2 route review ontology còn thiếu coverage, bằng cách seed candidate hợp lệ vào DB rồi gọi API review/publish.

Thiết lập chính:

- `DEFAULT_PROVIDER=openrouter`
- `DEFAULT_MODEL=nvidia/nemotron-3-super-120b-a12b:free`
- `ONTOLOGY_LLM_PROVIDER=openrouter`
- `ONTOLOGY_LLM_MODEL=nvidia/nemotron-3-super-120b-a12b:free`
- `DATABASE_URL=sqlite+pysqlite:///:memory:`
- `CELERY_TASK_ALWAYS_EAGER=true`
- `NEO4J_ENABLED=false`

Lưu ý quan trọng:

- Không phải mọi API đều thực sự gọi model.
- Các API cấu hình, documents, retrieval, tools, ontology review/publish chủ yếu kiểm thử backend contract dưới cấu hình OpenRouter.
- Những API thực sự dùng LLM trong lượt này là chat/runtime path.

## 3. Kết quả theo nhóm API

### 3.1. Hạ tầng và cấu hình

Pass:

- `GET /health`
- `GET /api/v1/auth/me`
- `GET /api/v1/agents/settings`
- `PUT /api/v1/agents/settings`
- `GET /api/v1/agents/tasks`
- `GET /api/v1/agents/catalog`
- `GET /api/v1/models`
- `GET /api/v1/providers/models`
- `GET /api/v1/providers/{provider}/models`
- `GET /api/v1/agents/profiles`
- `POST /api/v1/agents/profiles`
- `GET /api/v1/agents/profiles/{profile_id}`
- `PATCH /api/v1/agents/profiles/{profile_id}`
- `POST /api/v1/agents/profiles/{profile_id}/set-default`

Ghi nhận:

- Endpoint provider models trả về được catalog OpenRouter.
- Model mục tiêu `nvidia/nemotron-3-super-120b-a12b:free` xuất hiện trong response catalog dưới tên `NVIDIA: Nemotron 3 Super (free)`.

### 3.2. Documents và retrieval

Pass:

- `POST /api/v1/documents/upload` cho đủ 4 loại: `pdf`, `docx`, `xlsx`, `csv`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/jobs`
- `POST /api/v1/documents/{document_id}/reprocess`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/retrieval/reindex`

Ghi nhận:

- Upload PDF thành công, document được index với `parser_version = pypdf-fast-fallback-v1`.
- Upload CSV thành công, document được index với `parser_version = csv-structured-v1`.
- Retrieval trả citation đúng anchor mới:
  - PDF trả `page 1`
  - CSV trả `rows 2-4`

Ví dụ thực tế:

- Query PDF: `Which program requires approval?`
  - trả chunk có excerpt `Alpha program requires approval on page one.`
  - citation: `page 1`
- Query CSV: `What revenue did East have in January?`
  - trả chunk có row range `2-4`
  - citation: `rows 2-4`

### 3.3. Conversations, chat, task runtime, workflow runtime

Pass:

- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `PATCH /api/v1/conversations/{conversation_id}/model-selection`
- `PATCH /api/v1/conversations/{conversation_id}/agent-profile`
- `POST /api/v1/chat/messages`
- `POST /api/v1/tasks/resolve`
- `GET /api/v1/workflows`
- `POST /api/v1/workflows/{workflow_id}/run`

Xác nhận OpenRouter chạy thật:

- `POST /api/v1/chat/messages` dùng `provider=openrouter`, `model=nvidia/nemotron-3-super-120b-a12b:free`
- Response trả về `OK` đúng như prompt kiểm thử
- Latency đo được trong lượt chạy chính: khoảng `19.7 giây`

Ghi nhận cho runtime task/workflow:

- `POST /api/v1/tasks/resolve`
- `POST /api/v1/workflows/task.resolve.chat/run`

đều pass, nhưng kết quả là:

- `No indexed document or graph context matched that question.`

Điều này là hợp lý trong context test vì path này hiện vẫn ưu tiên evidence hiện có trong workspace/graph; nó không chứng minh ontology/web/tool loop đã hoàn thiện.

### 3.4. Tools API

Pass:

- `GET /api/v1/tools`
- `POST /api/v1/tools/{tool_name}/invoke`

Ghi nhận:

- `retrieval.internal` invoke thành công
- Tool result trả đầy đủ envelope:
  - `call_id`
  - `status`
  - `started_at`
  - `finished_at`
  - `latency_ms`
  - `evidence`
  - `meta`
- Evidence cho PDF đã có `citation_anchor.anchor_type = page`

### 3.5. Ontology API

Pass trong lượt chạy chính:

- `POST /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds/{build_id}`
- `GET /api/v1/ontology/builds/{build_id}/entities`
- `GET /api/v1/ontology/builds/{build_id}/relations`
- `GET /api/v1/ontology/graph`

Pass trong lượt chạy bổ sung:

- `POST /api/v1/ontology/entities/{entity_id}/review`
- `POST /api/v1/ontology/relations/{relation_id}/review`
- `POST /api/v1/ontology/builds/{build_id}/publish`

Kết quả đáng chú ý:

- Build ontology tạo thành công nhưng `entity_count = 0`, `relation_count = 0`
- `publish` ở lượt chạy chính trả `400` với message:
  - `Ontology build '...' has no approved entities to publish.`
- Đây là phản hồi nghiệp vụ đúng, không phải crash

Sau khi seed candidate hợp lệ và approve qua API:

- Review entity: `200`
- Review relation: `200`
- Publish build: `200`
- Graph get sau publish: `200`

## 4. Hai phát hiện kỹ thuật quan trọng

### 4.1. OpenRouter hoạt động tốt ở chat/runtime model path

Điểm này đã được xác nhận bằng request thật:

- `POST /api/v1/chat/messages`
- conversation lưu đúng:
  - `provider = openrouter`
  - `model = nvidia/nemotron-3-super-120b-a12b:free`
- assistant trả lời đúng output mong đợi

Điều này chứng minh adapter/model routing cho OpenRouter đang usable ở runtime chat path.

### 4.2. Ontology extractor hiện chưa thực sự hỗ trợ OpenRouter

Đây là giới hạn lớn nhất của lượt test này.

Trong file:

- `apps/backend/src/semantic_reasoning_agent/infrastructure/ontology/llm_extractor.py`

code hiện kiểm tra:

- chỉ tiếp tục khi `provider == "anthropic"`

Hệ quả:

- dù cấu hình `ONTOLOGY_LLM_PROVIDER=openrouter`
- ontology build vẫn không dùng OpenRouter để sinh entity/relation candidate
- build hoàn thành nhưng ra `0 entity`, `0 relation`

Vì vậy:

- các route ontology vẫn hoạt động đúng ở mức API contract
- nhưng “OpenRouter-backed ontology extraction” hiện chưa được triển khai thực sự trong codebase

## 5. Danh sách route đã phủ kín

Đã kiểm thử đủ `40/40` route-method dưới `/api/v1`:

- `GET /api/v1/agents/catalog`
- `GET /api/v1/agents/profiles`
- `POST /api/v1/agents/profiles`
- `GET /api/v1/agents/profiles/{profile_id}`
- `PATCH /api/v1/agents/profiles/{profile_id}`
- `POST /api/v1/agents/profiles/{profile_id}/set-default`
- `GET /api/v1/agents/settings`
- `PUT /api/v1/agents/settings`
- `GET /api/v1/agents/tasks`
- `GET /api/v1/auth/me`
- `POST /api/v1/chat/messages`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `PATCH /api/v1/conversations/{conversation_id}/agent-profile`
- `PATCH /api/v1/conversations/{conversation_id}/model-selection`
- `GET /api/v1/documents`
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/jobs`
- `POST /api/v1/documents/{document_id}/reprocess`
- `GET /api/v1/models`
- `POST /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds`
- `GET /api/v1/ontology/builds/{build_id}`
- `GET /api/v1/ontology/builds/{build_id}/entities`
- `POST /api/v1/ontology/builds/{build_id}/publish`
- `GET /api/v1/ontology/builds/{build_id}/relations`
- `POST /api/v1/ontology/entities/{entity_id}/review`
- `GET /api/v1/ontology/graph`
- `POST /api/v1/ontology/relations/{relation_id}/review`
- `GET /api/v1/providers/models`
- `GET /api/v1/providers/{provider}/models`
- `POST /api/v1/retrieval/reindex`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/tasks/resolve`
- `GET /api/v1/tools`
- `POST /api/v1/tools/{tool_name}/invoke`
- `GET /api/v1/workflows`
- `POST /api/v1/workflows/{workflow_id}/run`

## 6. Đánh giá cuối cùng

Ở mức API/backend contract, hệ thống đang ổn:

- document ingestion pass
- retrieval pass
- tools API pass
- conversations/chat pass
- task/workflow entrypoints pass
- ontology review/publish endpoints pass

Điểm chưa ổn nằm ở tầng nghiệp vụ ontology dùng LLM:

- với cấu hình OpenRouter hiện tại, build ontology không sinh candidate thật
- nguyên nhân không phải do OpenRouter API hỏng
- nguyên nhân là implementation hiện tại khóa ontology extractor vào Anthropic

## 7. Kiến nghị tiếp theo

1. Ưu tiên mở `OpenDomainLLMExtractor` để hỗ trợ `openrouter` thay vì hardcode Anthropic.
2. Sau khi mở extractor, chạy lại bộ test ontology end-to-end mà không seed tay candidate.
3. Nếu muốn biến báo cáo này thành regression artifact, nên thêm script kiểm thử API chính thức vào repo và lưu raw result dưới dạng JSON/Markdown ổn định.
