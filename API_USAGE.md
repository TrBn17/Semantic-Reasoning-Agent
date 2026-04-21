# Hướng Dẫn Sử Dụng API Backend

Ngày xác minh live: `2026-04-21`  
Môi trường xác minh: Docker local, backend restart lại để nạp `OPENROUTER_API_KEY` từ `.env`  
Provider AI xác minh: `openrouter`  
Model AI xác minh: `minimax/minimax-m2.5:free`

## 1. Tài liệu này dành cho ai

Tài liệu này dành cho:

- frontend dev cần nối UI vào backend
- người làm no-code / automation cần biết gọi API theo flow nghiệp vụ
- QA / PM cần phân biệt endpoint nào trả kết quả ngay, endpoint nào chỉ tạo job/build rồi phải poll tiếp

Tài liệu này không đi theo kiểu liệt kê toàn bộ route thuần kỹ thuật. Nó đi theo luồng nghiệp vụ thật đã được kiểm tra live.

## 2. Kết luận nhanh

Backend hiện tại hoạt động tốt nhất nếu bạn hiểu nó theo các flow sau:

- xác định người dùng và workspace hiện hành
- kiểm tra provider/model đã sẵn sàng chưa
- tạo conversation rồi gửi chat
- upload document rồi chờ ingestion/index hoàn tất
- chạy retrieval hoặc `tasks/resolve` để lấy câu trả lời có grounding
- tạo ontology build, review candidate, rồi publish graph
- dùng `tools` và `workflows` như lớp runtime/registry, không phải mọi workflow đều chạy trực tiếp được

Các điểm đã xác minh live ngày `2026-04-21`:

- Sau khi restart backend, `GET /api/v1/agents/settings`, `GET /api/v1/models`, và `GET /api/v1/providers/openrouter/models` đều thấy `openrouter` là runtime-ready.
- Catalog OpenRouter có model `minimax/minimax-m2.5:free`.
- `POST /api/v1/chat/messages` trả đúng `OPENROUTER_CHAT_OK` khi dùng `openrouter + minimax/minimax-m2.5:free`.
- `POST /api/v1/tasks/resolve` fallback sang OpenRouter thành công và trả đúng `TASK_RESOLVE_OPENROUTER_OK` khi không có evidence nội bộ.
- `POST /api/v1/ontology/builds` với task `ontology_extraction=openrouter/minimax/minimax-m2.5:free` đã gọi thật tới OpenRouter trong worker và hoàn tất build thành công.

## 3. Flow 1: Xác định danh tính và workspace hiện hành

### Mục tiêu

Frontend cần biết user hiện tại đang ở workspace nào để dùng đúng `workspace_id`.

### Endpoint chính

- `GET /api/v1/auth/me`

### Dùng khi nào

- lúc app boot
- lúc refresh layout chính
- trước khi gọi các flow cần `workspace_id`

### Kết quả nhận về

Trả ngay dữ liệu đồng bộ:

- `id`
- `email`
- `display_name`
- `active_workspace.id`
- `active_workspace.name`

### Gợi ý cho frontend

- Nếu UI của bạn chỉ có một workspace mặc định, hãy cache `active_workspace.id`.
- Nếu request khác không truyền `workspace_id`, backend thường fallback về workspace mặc định này.

## 4. Flow 2: Kiểm tra provider/model có chạy được chưa

Đây là flow quan trọng nhất trước khi gọi chat hoặc task fallback AI.

### Endpoint nên đọc theo thứ tự

1. `GET /api/v1/agents/settings`
2. `GET /api/v1/models`
3. `GET /api/v1/providers/openrouter/models`
4. `PUT /api/v1/agents/settings` khi cần bật provider hoặc đổi model theo task

### Ý nghĩa từng endpoint

`GET /api/v1/agents/settings`

- endpoint tổng hợp tốt nhất cho frontend settings screen
- cho biết:
  - provider nào đang `enabled`
  - provider nào `ready`
  - field nào còn thiếu
  - task nào đang gán model nào

`GET /api/v1/models`

- catalog model đã được merge với trạng thái readiness cho workspace hiện tại
- frontend picker nên ưu tiên nguồn này nếu muốn hiển thị model “chọn được ngay”

`GET /api/v1/providers/{provider}/models`

- gọi trực tiếp provider để lấy catalog live
- phù hợp khi người dùng muốn refresh model list mới nhất
- với OpenRouter, endpoint này đã live trả được `minimax/minimax-m2.5:free`

`PUT /api/v1/agents/settings`

- lưu cấu hình provider theo workspace
- lưu gán model theo `task_type`
- trong kiểm thử live, cần gọi endpoint này để bật `openrouter` trong workspace trước khi `chat/messages` và `tasks/resolve` coi provider là ready

### Điều đã xác minh live

Trước khi restart backend:

- `GET /api/v1/agents/settings` báo `openrouter` chưa có `OPENROUTER_API_KEY`
- `GET /api/v1/providers/openrouter/models` trả lỗi thiếu key

Sau khi restart backend ngày `2026-04-21`:

- `openrouter` chuyển sang `ready=true`
- `GET /api/v1/providers/openrouter/models` trả catalog live
- catalog có `minimax/minimax-m2.5:free`

### Payload mẫu để bật OpenRouter cho workspace

```json
{
  "workspace_id": "workspace-demo",
  "providers": [
    {
      "provider": "openrouter",
      "enabled": true,
      "values": {}
    }
  ],
  "task_assignments": [
    {
      "task_type": "chat",
      "provider": "openrouter",
      "model": "minimax/minimax-m2.5:free"
    },
    {
      "task_type": "ontology_extraction",
      "provider": "openrouter",
      "model": "minimax/minimax-m2.5:free"
    }
  ]
}
```

### Lưu ý rất quan trọng

- Lưu secret/cấu hình qua `PUT /api/v1/agents/settings` không thay thế được việc backend process phải nạp adapter lúc startup.
- Nếu `.env` đã có `OPENROUTER_API_KEY` nhưng runtime vẫn không thấy, cần restart backend process/container.

## 5. Flow 3: Tạo conversation và gửi chat

### Mục tiêu

Dùng khi UI của bạn là chat interface có lịch sử hội thoại.

### Trình tự chuẩn

1. `POST /api/v1/conversations`
2. tùy chọn: `PATCH /api/v1/conversations/{conversation_id}/model-selection`
3. `POST /api/v1/chat/messages`
4. `GET /api/v1/conversations/{conversation_id}` nếu muốn reload thread

### Endpoint nào trả dữ liệu ngay

Đều là đồng bộ:

- conversation được tạo ngay
- message assistant được trả ngay trong response của `POST /chat/messages`

### Điều đã xác minh live

Conversation:

- tạo conversation với `provider=openrouter`, `model=minimax/minimax-m2.5:free`

Chat:

- gửi prompt `Reply with exactly: OPENROUTER_CHAT_OK`
- backend trả đúng `OPENROUTER_CHAT_OK`

### Khi nào nên dùng chat

- cần lưu lịch sử hội thoại
- cần gắn model override vào từng conversation
- cần UI chat truyền thống

### Khi nào không nên dùng chat

- nếu bạn chỉ cần một lần resolve task không cần thread lịch sử
- khi đó dùng `POST /api/v1/tasks/resolve`

## 6. Flow 4: Resolve task kiểu “một phát ăn ngay”

### Mục tiêu

Dùng khi bạn không cần conversation nhưng vẫn muốn backend:

- thử retrieval nội bộ
- đọc ontology/graph
- nếu không đủ evidence thì fallback sang model AI

### Endpoint chính

- `POST /api/v1/tasks/resolve`

### Hành vi hiện tại

- nếu có document evidence, response sẽ trả `content` dạng grounded summary + `citations` + `evidence`
- nếu không có evidence nội bộ nhưng request truyền `provider/model` hợp lệ, backend có thể fallback sang LLM

### Điều đã xác minh live

Không có evidence nội bộ:

- request với `provider=openrouter`, `model=minimax/minimax-m2.5:free`
- prompt: `Reply with exactly: TASK_RESOLVE_OPENROUTER_OK`
- response trả đúng `TASK_RESOLVE_OPENROUTER_OK`

Có evidence nội bộ:

- query: `What depends on Beta system?`
- response trả:
  - `content` có `Relevant context:`
  - `citations`
  - `evidence`

### Khi nào nên dùng

- backend-for-frontend cần một API “answer this task now”
- no-code automation muốn ít state hơn chat

## 7. Flow 5: Upload document, theo dõi ingestion, retrieval, và reindex

### Mục tiêu

Cho phép người dùng upload tài liệu vào workspace, sau đó search/retrieve được.

### Trình tự chuẩn

1. `POST /api/v1/documents/upload`
2. poll `GET /api/v1/documents/{id}`
3. đọc `GET /api/v1/documents/{id}/jobs`
4. gọi `POST /api/v1/retrieval/search`
5. nếu cần xử lý lại: `POST /api/v1/documents/{id}/reprocess` hoặc `POST /api/v1/retrieval/reindex`

### Phân loại sync vs async

`POST /api/v1/documents/upload`

- trả ngay document record
- không đảm bảo file đã index xong ở ngay response đầu tiên

`GET /api/v1/documents/{id}`

- dùng để xem `status`: `uploaded`, `parsed`, `indexed`, `failed`

`GET /api/v1/documents/{id}/jobs`

- dùng để xem chi tiết pipeline:
  - `parse_document`
  - `build_chunks`
  - `embed_chunks`
  - `upsert_qdrant`

`POST /api/v1/retrieval/search`

- đồng bộ
- trả kết quả retrieval ngay nếu document đã index

`POST /api/v1/retrieval/reindex`

- API hiện tại trả về danh sách document id đã yêu cầu reindex
- với môi trường live đang chạy worker, document sẽ được xử lý lại nền sau đó

### Điều đã xác minh live

CSV hợp lệ:

- upload file CSV thành công
- document chuyển sang `indexed`
- `parser_version=csv-structured-v1`
- `chunk_count=2`
- cả 4 job đều `completed`

Retrieval:

- query `What depends on Beta system?`
- result trả citation `rows 2-3`

Tool invoke:

- `POST /api/v1/tools/retrieval.internal/invoke` trả đầy đủ tool envelope và evidence

### Lỗi nghiệp vụ thực tế đã gặp

Upload DOCX lỗi cấu trúc:

- backend trả trạng thái document `failed`
- `error_message`:
  - `"no relationship of type 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument' in collection"`

Ý nghĩa:

- file `.docx` không phải DOCX hợp lệ theo OpenXML
- caller nên export lại từ Word / LibreOffice / Google Docs thay vì tự đổi đuôi file

## 8. Flow 6: Build ontology, review, publish, đọc graph

### Mục tiêu

Biến document đã index thành:

- candidate entities
- candidate relations
- ontology version đã publish
- graph đọc được qua API

### Trình tự chuẩn

1. `POST /api/v1/ontology/builds`
2. poll `GET /api/v1/ontology/builds/{build_id}`
3. đọc `GET /api/v1/ontology/builds/{build_id}/entities`
4. đọc `GET /api/v1/ontology/builds/{build_id}/relations`
5. approve qua:
   - `POST /api/v1/ontology/entities/{entity_id}/review`
   - `POST /api/v1/ontology/relations/{relation_id}/review`
6. `POST /api/v1/ontology/builds/{build_id}/publish`
7. `GET /api/v1/ontology/graph`

### Đây là flow async

`POST /api/v1/ontology/builds`

- chỉ tạo build record
- trong live run, response đầu là `status=pending`

Bạn phải poll `GET /api/v1/ontology/builds/{id}` để biết:

- đang ở bước nào
- đã hoàn tất chưa
- có lỗi không

### Điều đã xác minh live với OpenRouter

Sau khi gán:

- `task_type=ontology_extraction`
- `provider=openrouter`
- `model=minimax/minimax-m2.5:free`

thì build ontology trên file CSV đã cho kết quả:

- worker gọi thật `https://openrouter.ai/api/v1/chat/completions`
- build hoàn tất `completed`
- `entity_count=6`
- `relation_count=6`
- candidate provenance có:
  - `extractor=open_domain_llm`
  - `provider=openrouter`
  - `model=minimax/minimax-m2.5:free`

Thời gian live run:

- khoảng `308` giây cho bước `extract_entities`

### Publish flow

Sau khi approve toàn bộ candidate:

- `POST /api/v1/ontology/builds/{id}/publish` thành công
- tạo version `1`
- `GET /api/v1/ontology/graph` trả graph snapshot đã publish

### Lưu ý cho frontend

- build tạo candidate chứ không tự publish
- publish bị chặn nếu chưa có candidate được approve
- UI cần có màn review, không nên giả định build xong là graph đã public

## 9. Flow 7: Workflows và tools

### Workflows

`GET /api/v1/workflows` hiện trả registry gồm:

- `task.resolve.chat`
- `ontology.build`
- `ontology.publish`

Trạng thái thực tế:

- `task.resolve.chat`: chạy trực tiếp được qua `POST /api/v1/workflows/task.resolve.chat/run`
- `ontology.build`: hiện là workflow registry/metadata, không chạy trực tiếp qua `/workflows/{id}/run`
- `ontology.publish`: hiện là workflow registry/metadata, không chạy trực tiếp qua `/workflows/{id}/run`

### Tools

`GET /api/v1/tools` live hiện trả:

- `retrieval.internal`
- `ontology.lookup`
- `graphiti.search`
- `graphiti.ingest_episode`

Trạng thái thực tế:

- `retrieval.internal`: operational, đã invoke live thành công
- `ontology.lookup`: operational khi đã có ontology published
- `graphiti.search`: operational nhưng trong môi trường live hiện có hint `graphiti_disabled`
- `graphiti.ingest_episode`: có trong registry, là write-internal tool mức `medium`, không phải luồng người dùng phổ thông đầu tiên

### Khi nào frontend nên dùng `tools`

- admin/debug UI
- internal ops console
- không phải lựa chọn đầu tiên cho end-user UI bình thường

### Khi nào frontend nên dùng `workflows`

- khi bạn muốn gọi runtime ở cấp workflow thay vì từng tool
- hiện tại endpoint runnable thực tế là `task.resolve.chat`

## 10. Bảng tóm tắt sync vs async

### Trả dữ liệu hoàn chỉnh ngay

- `GET /api/v1/auth/me`
- `GET /api/v1/agents/settings`
- `PUT /api/v1/agents/settings`
- `GET /api/v1/models`
- `GET /api/v1/providers/{provider}/models`
- `POST /api/v1/conversations`
- `POST /api/v1/chat/messages`
- `POST /api/v1/tasks/resolve`
- `POST /api/v1/retrieval/search`
- `GET /api/v1/tools`
- `POST /api/v1/tools/{tool_name}/invoke`
- `GET /api/v1/workflows`
- `POST /api/v1/workflows/task.resolve.chat/run`
- `GET /api/v1/ontology/graph`

### Tạo record/job/build rồi phải theo dõi tiếp

- `POST /api/v1/documents/upload`
- `POST /api/v1/documents/{id}/reprocess`
- `POST /api/v1/retrieval/reindex`
- `POST /api/v1/ontology/builds`

### Thường cần poll sau khi gọi async endpoint

- `GET /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/jobs`
- `GET /api/v1/ontology/builds/{id}`
- `GET /api/v1/ontology/builds/{id}/entities`
- `GET /api/v1/ontology/builds/{id}/relations`

## 11. Các lỗi nghiệp vụ thường gặp và nên làm gì tiếp

### `Provider '...' with model '...' is not ready yet.`

Nghĩa là:

- provider chưa được bật trong workspace, hoặc
- backend runtime chưa nạp env/API key, hoặc
- adapter runtime chưa tồn tại

Nên làm tiếp:

1. `GET /api/v1/agents/settings`
2. nếu cần, `PUT /api/v1/agents/settings`
3. nếu `.env` vừa đổi, restart backend process/container

### `OpenRouter API key not configured`

Nghĩa là:

- process hiện tại chưa thấy `OPENROUTER_API_KEY`

Nên làm tiếp:

1. kiểm tra `.env`
2. restart backend
3. gọi lại `GET /api/v1/providers/openrouter/models`

### `Uploaded file is empty.`

Nghĩa là:

- multipart upload không gửi được nội dung file thật

Nên làm tiếp:

- kiểm tra `Content-Type`, boundary, và binary body

### DOCX parse error kiểu `no relationship of type ... officeDocument`

Nghĩa là:

- file DOCX hỏng cấu trúc OpenXML

Nên làm tiếp:

- mở file bằng Word/LibreOffice rồi export lại DOCX chuẩn

### Publish ontology bị chặn vì chưa approve candidate

Nghĩa là:

- build xong nhưng review chưa hoàn tất

Nên làm tiếp:

1. đọc entities/relations
2. approve hoặc reject từng candidate
3. publish lại

### `Workflow '...' is not directly runnable via this endpoint yet.`

Nghĩa là:

- workflow có trong registry nhưng `/workflows/{id}/run` chưa support chạy trực tiếp cho workflow đó

Nên làm tiếp:

- dùng endpoint nghiệp vụ gốc, ví dụ `/ontology/builds` hoặc `/ontology/builds/{id}/publish`

## 12. Khuyến nghị triển khai cho frontend/no-code

- Với màn settings, lấy `GET /api/v1/agents/settings` làm nguồn sự thật chính.
- Với chat UI, luôn tạo conversation trước rồi mới gửi message.
- Với “ask one question now”, ưu tiên `POST /api/v1/tasks/resolve`.
- Với document UX, hiển thị rõ trạng thái ingest và job list thay vì giả định upload xong là search được ngay.
- Với ontology UX, thiết kế 3 màn riêng:
  - build status
  - candidate review
  - published graph
- Với OpenRouter, luôn kiểm tra catalog live qua `GET /api/v1/providers/openrouter/models` nếu cần picker model mới nhất.

## 13. Tóm tắt trạng thái hiện tại

Operational và đã xác minh live:

- auth/workspace identity
- agent settings và model catalog
- OpenRouter model discovery
- conversation + chat với `openrouter/minimax/minimax-m2.5:free`
- `tasks/resolve` fallback LLM
- document upload CSV + retrieval + reindex
- `tools/retrieval.internal/invoke`
- ontology build/review/publish/graph với OpenRouter
- workflow run cho `task.resolve.chat`

Registry hoặc support một phần:

- workflow registry cho `ontology.build` và `ontology.publish`
- graph-related tool path phụ thuộc runtime graph có bật hay không

