# Backend Flow Documentation

**Semantic Reasoning Agent - Backend Architecture & Code Flow**

Tài liệu này mô tả chi tiết cấu trúc, chức năng, và luồng xử lý của toàn bộ backend hệ thống.

---

## 📋 Mục Lục

1. [Tổng Quan Kiến Trúc](#tổng-quan-kiến-trúc)
2. [Cấu Trúc Thư Mục](#cấu-trúc-thư-mục)
3. [Chi Tiết Từng Module](#chi-tiết-từng-module)
4. [Luồng Xử Lý Chính](#luồng-xử-lý-chính)
5. [API Endpoints](#api-endpoints)
6. [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)

---

## 🏗️ Tổng Quan Kiến Trúc

Backend được xây dựng theo **Clean Architecture** với các lớp rõ ràng:

```
┌─────────────────────────────────────┐
│      API Layer (FastAPI)            │ ← HTTP Endpoints
├─────────────────────────────────────┤
│    Entrypoints (Routers)            │ ← Route handlers
├─────────────────────────────────────┤
│    Services Layer                   │ ← Business logic
├─────────────────────────────────────┤
│    Domain & Contracts               │ ← Domain models
├─────────────────────────────────────┤
│    Ports & Adapters                 │ ← Interfaces
├─────────────────────────────────────┤
│    Infrastructure                   │ ← External services
├─────────────────────────────────────┤
│    Persistence Layer                │ ← Database
└─────────────────────────────────────┘
```

**Stack Công Nghệ:**
- **Framework**: FastAPI (async HTTP framework)
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Task Queue**: Celery + Redis
- **Graph DB**: Neo4j (optional, for knowledge graph)
- **Vector Storage**: PostgreSQL (token-based vectors)
- **LLM Adapters**: Anthropic, OpenAI, Google, Ollama
- **File Parsers**: pypdf, python-docx, openpyxl

---

## 📁 Cấu Trúc Thư Mục

```
apps/backend/
├── src/semantic_reasoning_agent/
│   ├── main.py                      # FastAPI app initialization
│   ├── core/                        # Core configuration
│   ├── domain/                      # Domain models & contracts
│   ├── entrypoints/                 # HTTP API routes
│   ├── infrastructure/              # External service adapters
│   ├── persistence/                 # Database models & repos
│   ├── ports/                       # Port interfaces (abstract)
│   ├── schemas/                     # Pydantic request/response models
│   ├── services/                    # Business logic services
│   ├── tools/                       # Execution tools
│   └── workers/                     # Celery async tasks
├── worker/                          # Celery worker entrypoint
├── serve.py                         # Development server runner
└── alembic/                         # Database migrations
```

---

## 🔍 Chi Tiết Từng Module

### 1. **main.py** - Khởi Tạo FastAPI App

**Chức năng:**
- Khởi tạo FastAPI application instance
- Cấu hình CORS middleware
- Thiết lập database schema và migration
- Mount API routers

**Luồng xử lý:**
```python
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 1. Lấy database manager
    database_manager = get_database_manager()
    
    # 2. Tạo schema nếu chưa tồn tại
    database_manager.create_schema()
    
    # 3. Chạy Alembic migrations
    AlembicService(database_manager).upgrade()
    
    yield  # App chạy bình thường ở đây
    
    # 4. Cleanup khi app shutdown
```

**Endpoints cơ bản:**
- `GET /health` → Trả về `{"status": "ok"}`

---

### 2. **core/config.py** - Configuration Settings

**Chức năng:**
- Quản lý toàn bộ cấu hình ứng dụng
- Đọc từ biến môi trường (.env)
- Cải cache configuration (singleton)

**Các cấu hình quan trọng:**

| Cấu Hình | Mô Tả | Mặc Định |
|----------|-------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://semantic:semantic@localhost:5432/semantic_reasoning` |
| `CELERY_BROKER_URL` | Redis broker cho async tasks | `redis://localhost:6379/0` |
| `NEO4J_ENABLED` | Bật/tắt Neo4j integration | `false` |
| `ONTOLOGY_LLM_PROVIDER` | LLM provider cho ontology build | `anthropic` |
| `OBJECT_STORE_BACKEND` | Nơi lưu files | `postgres` (có thể là minio) |
| `VECTOR_STORE_BACKEND` | Backend vector search | `postgres` (có thể là qdrant) |
| `DEFAULT_WORKSPACE_ID` | Workspace mặc định | `workspace-demo` |

---

### 3. **core/container.py** - Dependency Injection

**Chức năng:**
- Quản lý lifecycle của services
- Cung cấp instances của dependencies
- Ánh xạ ports đến implementations

**Ví dụ:**
```python
# Register a service
container.register(ChatStreamService)

# Get instance khi cần
service = container.get(ChatStreamService)
```

---

### 4. **entrypoints/** - HTTP API Routes

**Chức năng:**
- Định nghĩa các HTTP endpoints
- Validation request inputs
- Xử lý error responses

**Cấu trúc:**

```
entrypoints/
├── router.py                  # Main API router
├── dependencies.py            # Dependency injection helpers
└── v1/                       # API v1 endpoints
    ├── agents.py            # Agent management
    ├── agent_profiles.py    # Agent profiles
    ├── auth.py              # Authentication
    ├── chat.py              # Chat messages
    ├── conversations.py     # Conversations
    ├── documents.py         # Document management
    ├── models.py            # Model configuration
    ├── ontology.py          # Ontology operations
    └── retrieval.py         # Search & retrieval
```

#### **4.1 chat.py - Chat Endpoints**

```python
@router.post("/messages")
def send_message(payload: SendMessageRequest) -> ChatReply:
    # 1. Kiểm tra conversation tồn tại
    # 2. Kiểm tra LLM provider/model ready
    # 3. Gọi LLM adapter để generate response
    # 4. Nếu use_retrieval=true, tìm relevant chunks
    # 5. Kết hợp retrieval results + LLM reply
    # 6. Lưu message vào conversation
    # 7. Return ChatReply với citations
```

**Request Schema:**
```python
class SendMessageRequest(BaseModel):
    conversation_id: str
    content: str
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    workspace_id: str | None = None
    document_ids: list[str] | None = None
    top_k: int = 3
```

**Response Schema:**
```python
class ChatReply(BaseModel):
    conversation: ConversationResponse
    reply: MessageResponse
    citations: list[Citation]
```

#### **4.2 documents.py - Document Management Endpoints**

```python
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    title: str | None = None,
    workspace_id: str | None = None,
    tags: str | None = None
) -> DocumentResponse:
    # 1. Đọc file content
    # 2. Kiểm tra file type (pdf, docx, xlsx)
    # 3. Lưu document record vào DB
    # 4. Queue document processing task
    # 5. Return DocumentResponse
```

**Luồng processing:**
1. **parse_document** → Phân tích file, extract text
2. **build_chunks** → Chia nhỏ text thành chunks
3. **embed_chunks** → Tính embedding cho mỗi chunk
4. **upsert_qdrant** → Lưu chunks vào vector store

```python
@router.get("")
def list_documents() -> list[DocumentResponse]:
    # Lấy tất cả documents từ DB, sort theo updated_at

@router.get("/{document_id}")
def get_document(document_id: str) -> DocumentResponse:
    # Lấy document chi tiết

@router.get("/{document_id}/jobs")
def get_document_jobs(document_id: str) -> list[DocumentJobResponse]:
    # Lấy danh sách jobs (parse, embed, etc)

@router.post("/{document_id}/reprocess")
def reprocess_document(document_id: str) -> DocumentReprocessResponse:
    # Reset chunks, re-queue processing tasks
```

#### **4.3 retrieval.py - Search Endpoints**

```python
@router.post("/search")
def search(query: str, workspace_id: str | None = None) -> RetrievalSearchResponse:
    # 1. Tính embedding cho query
    # 2. Tìm k chunks tương tự nhất
    # 3. Tính cosine similarity score
    # 4. Tạo citations
    # 5. Return results
```

#### **4.4 ontology.py - Ontology Endpoints**

```python
@router.post("/builds")
def create_ontology_build(payload: OntologyBuildRequest) -> OntologyBuildResponse:
    # 1. Tạo OntologyBuild record
    # 2. Queue processing task

@router.get("/builds")
def list_builds() -> list[OntologyBuildResponse]:
    # Lấy danh sách builds

@router.post("/builds/{build_id}/publish")
def publish_build(build_id: str) -> OntologyBuildResponse:
    # 1. Copy candidates → approved version
    # 2. Sync to Neo4j (nếu enabled)
    # 3. Return published build
```

---

### 5. **services/** - Business Logic Layer

**Chức năng:**
- Implement business logic
- Orchestrate lower layers
- Transaction management

```
services/
├── chat_stream_service.py       # Chat message handling
├── conversation_service.py      # Conversation CRUD
├── document_service.py          # Document ingestion
├── retrieval_service.py         # Vector search
├── ontology_service.py          # Ontology build
├── model_config_service.py      # LLM configuration
├── agent_profile_service.py     # Agent profiles
├── secret_service.py            # API key management
└── alembic_service.py           # Database migrations
```

#### **5.1 ChatStreamService**

**Mục đích:** Xử lý message từ user, generate reply, retrieve citations

**Key Methods:**

```python
class ChatStreamService:
    def send_message(self, payload: SendMessageRequest) -> ChatReply:
        # 1. Lấy conversation
        conversation = self._conversation_service.get_conversation(
            payload.conversation_id
        )
        
        # 2. Xác định provider/model
        runtime_provider = payload.provider or conversation.provider
        runtime_model = payload.model or conversation.model
        
        # 3. Kiểm tra LLM ready
        if not self._model_config_service.is_ready(
            runtime_provider, runtime_model, workspace_id
        ):
            raise ProviderNotReadyError(f"Provider not ready")
        
        # 4. Lấy LLM adapter
        adapter = self._adapter_registry.get(runtime_provider)
        
        # 5. Lưu user message
        self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="user",
            content=payload.content
        )
        
        # 6. Generate LLM reply
        reply_text = adapter.generate_reply(
            payload.content,
            system_prompt=system_prompt
        )
        
        # 7. Nếu use_retrieval, tìm citations
        citations = []
        if payload.use_retrieval:
            search_response = self._retrieval_service.search(
                query=payload.content,
                workspace_id=workspace_id,
                top_k=payload.top_k
            )
            citations = [r.citation for r in search_response.results]
            
            # Kết hợp citations vào reply
            if citations:
                reply_text = self._compose_grounded_reply(
                    payload.content,
                    citations
                )
        
        # 8. Lưu assistant message
        updated = self._conversation_service.append_message(
            conversation_id=payload.conversation_id,
            role="assistant",
            content=reply_text
        )
        
        # 9. Return ChatReply
        return ChatReply(
            conversation=updated,
            reply=updated.messages[-1],
            citations=citations
        )
    
    @staticmethod
    def _compose_grounded_reply(prompt: str, citations: list[Citation]) -> str:
        """Kết hợp citations vào reply trả về"""
        lines = [f"Question: {prompt}", "Relevant context:"]
        for citation in citations:
            lines.append(
                f"- {citation.document_title} "
                f"({citation.location_label}): {citation.excerpt}"
            )
        return "\n".join(lines)
```

#### **5.2 DocumentService**

**Mục đích:** Quản lý lifecycle của documents

**Key Methods:**

```python
class DocumentService:
    def upload_document(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        workspace_id: str | None = None,
        tags: list[str] | None = None
    ) -> DocumentResponse:
        # 1. Kiểm tra file type hợp lệ
        if not self._is_supported_document(filename):
            raise UnsupportedDocumentTypeError(f"Type not supported")
        
        # 2. Tạo document ID
        document_id = str(uuid4())
        resolved_workspace_id = workspace_id or settings.default_workspace_id
        timestamp = utc_now()
        
        # 3. Lưu file binary
        stored_content = self._object_store.put_document_binary(
            document_id, content
        )
        
        # 4. Tạo DocumentORM record
        document = DocumentORM(
            id=document_id,
            title=title or Path(filename).stem,
            filename=filename,
            workspace_id=resolved_workspace_id,
            document_type=Path(filename).suffix.lower().lstrip("."),
            status=DocumentStatus.uploaded.value,
            parser_version=PARSER_VERSION,
            chunk_count=0,
            source_url=f"db://{workspace_id}/{document_id}/{filename}",
            binary_content=stored_content,
            created_at=timestamp,
            updated_at=timestamp
        )
        
        # 5. Lưu vào DB
        with self._database_manager.session() as session:
            session.add(document)
            # 6. Tạo job records
            session.add_all(self._build_job_records(document_id))
        
        # 7. Queue document processing
        self._queue_document(document_id)
        
        return self.get_document(document_id)
    
    def reprocess_document(self, document_id: str) -> DocumentReprocessResponse:
        """Reprocess document: xóa chunks cũ, re-queue"""
        self._ensure_document_exists(document_id)
        self._prepare_reprocess(document_id)
        self._queue_document(document_id)
        return DocumentReprocessResponse(
            document=self.get_document(document_id),
            jobs=self.get_document_jobs(document_id)
        )
```

**Pipeline Jobs:**
1. `parse_document` - Parse file, extract text
2. `build_chunks` - Chia nhỏ text
3. `embed_chunks` - Tính embeddings
4. `upsert_qdrant` - Lưu vào vector store

#### **5.3 RetrievalService**

**Mục đích:** Vector search, retrieval, citations

**Key Methods:**

```python
class RetrievalService:
    def prepare_document_chunks(
        self,
        document: DocumentResponse,
        parsed_document: ParsedDocument
    ) -> list[IndexedChunk]:
        """Chuẩn bị chunks từ parsed document"""
        prepared_chunks = []
        for chunk in parsed_document.chunks:
            prepared_chunks.append(
                IndexedChunk(
                    chunk_id=str(uuid4()),
                    document_id=document.id,
                    workspace_id=document.workspace_id,
                    text=chunk.text,
                    # ... other fields
                    embedding=self.embed_text(chunk.text),
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    heading_path=chunk.heading_path,
                    sheet_name=chunk.sheet_name,
                    row_start=chunk.row_start,
                    row_end=chunk.row_end,
                )
            )
        return prepared_chunks
    
    def upsert_chunks(self, document_id: str, chunks: list[IndexedChunk]) -> None:
        """Lưu chunks vào database"""
        with self._database_manager.session() as session:
            # Xóa chunks cũ
            session.execute(
                delete(DocumentChunkORM)
                .where(DocumentChunkORM.document_id == document_id)
            )
            # Thêm chunks mới
            for chunk in chunks:
                session.add(DocumentChunkORM(...))
    
    def search(
        self,
        query: str,
        workspace_id: str | None = None,
        document_ids: list[str] | None = None,
        top_k: int = 3
    ) -> RetrievalSearchResponse:
        """Tìm kiếm chunks tương tự"""
        resolved_workspace_id = workspace_id or settings.default_workspace_id
        
        # 1. Lấy tất cả chunks từ DB
        with self._database_manager.session() as session:
            statement = select(DocumentChunkORM).where(
                DocumentChunkORM.workspace_id == resolved_workspace_id
            )
            if document_ids:
                statement = statement.where(
                    DocumentChunkORM.document_id.in_(document_ids)
                )
            chunks = session.scalars(statement).all()
        
        # 2. Tính embedding của query
        query_embedding = self.embed_text(query)
        
        # 3. Tính similarity với mỗi chunk
        matches = []
        for chunk in chunks:
            score = self._vector_backend.cosine_similarity(
                query_embedding,
                chunk.embedding
            )
            if score > 0:
                matches.append((chunk, score))
        
        # 4. Sort theo score, lấy top k
        matches.sort(key=lambda x: x[1], reverse=True)
        matches = matches[:top_k]
        
        # 5. Tạo results
        results = [
            RetrievalResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_title=chunk.document_title,
                score=round(score, 6),
                excerpt=excerpt(chunk.text),
                citation=self._build_citation(chunk)
            )
            for chunk, score in matches
        ]
        
        return RetrievalSearchResponse(query=query, results=results)
    
    def embed_text(self, text: str) -> dict[str, int]:
        """Tính embedding (token vectors)"""
        return self._vector_backend.embed_text(text)
    
    def _build_citation(self, chunk: DocumentChunkORM) -> Citation:
        """Tạo citation object từ chunk"""
        location_label = "document"
        if chunk.document_type == "pdf" and chunk.page_number:
            location_label = f"page {chunk.page_number}"
        elif chunk.document_type == "docx" and chunk.heading_path:
            location_label = chunk.heading_path
        elif chunk.document_type == "xlsx":
            location_label = (
                f"{chunk.sheet_name} rows {chunk.row_start}-{chunk.row_end}"
            )
        return Citation(
            document_id=chunk.document_id,
            document_title=chunk.document_title,
            excerpt=excerpt(chunk.text),
            location_label=location_label,
            source_url=chunk.source_url
        )
```

---

### 6. **persistence/** - Database Layer

**Chức năng:**
- SQLAlchemy ORM models
- Database schema
- Repository pattern

```
persistence/
├── database.py                  # Database manager
├── models/
│   ├── base.py                 # Base ORM class
│   ├── conversations.py        # Conversations table
│   ├── documents.py            # Documents table
│   ├── ontology.py             # Ontology tables
│   ├── providers.py            # Provider config
│   └── agent_profiles.py       # Agent profiles
└── repositories/               # Future: specific repos
```

#### **6.1 database.py - DatabaseManager**

```python
class DatabaseManager:
    """Quản lý database connection & operations"""
    
    def __init__(self, settings: Settings):
        self._settings = settings
        # Tạo engine dựa trên DATABASE_URL
        self.engine = self._build_engine(settings)
        # Session factory
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False
        )
    
    @contextmanager
    def session(self) -> Iterator[Session]:
        """Context manager để lấy DB session"""
        session = self._session_factory()
        try:
            yield session
            session.commit()  # Auto commit nếu không có exception
        except Exception:
            session.rollback()  # Rollback nếu có lỗi
            raise
        finally:
            session.close()
    
    def create_schema(self) -> None:
        """Tạo schema từ Base.metadata"""
        Base.metadata.create_all(self.engine)
    
    def drop_schema(self) -> None:
        """Xóa toàn bộ schema"""
        Base.metadata.drop_all(self.engine)
    
    def reset_schema(self) -> None:
        """Reset: drop + create"""
        self.drop_schema()
        self.create_schema()
```

#### **6.2 Models - ORM Classes**

**Documents Model:**
```python
class DocumentORM(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    filename: Mapped[str]
    workspace_id: Mapped[str]
    document_type: Mapped[str]  # pdf, docx, xlsx
    status: Mapped[str]          # uploaded, processing, ready
    parser_version: Mapped[str]
    chunk_count: Mapped[int]
    tags: Mapped[list[str]]
    source_url: Mapped[str]
    binary_content: Mapped[bytes | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    error_message: Mapped[str | None]
    
    # Relations
    jobs: Mapped[list[DocumentJobORM]] = relationship(back_populates="document")
    chunks: Mapped[list[DocumentChunkORM]] = relationship(back_populates="document")
```

**DocumentJob Model:**
```python
class DocumentJobORM(Base):
    __tablename__ = "document_jobs"
    
    id: Mapped[str]
    document_id: Mapped[str]
    job_name: Mapped[str]  # parse, embed, index
    status: Mapped[str]     # pending, running, done, error
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    error_message: Mapped[str | None]
    
    # Relations
    document: Mapped[DocumentORM] = relationship(back_populates="jobs")
```

**DocumentChunk Model:**
```python
class DocumentChunkORM(Base):
    __tablename__ = "document_chunks"
    
    chunk_id: Mapped[str] = mapped_column(primary_key=True)
    document_id: Mapped[str]
    workspace_id: Mapped[str]
    document_title: Mapped[str]
    text: Mapped[str]
    chunk_index: Mapped[int]
    source_url: Mapped[str]
    embedding: Mapped[dict]      # Token vector
    
    # PDF specific
    page_number: Mapped[int | None]
    
    # DOCX specific
    section_title: Mapped[str | None]
    heading_path: Mapped[str | None]
    
    # XLSX specific
    sheet_name: Mapped[str | None]
    table_index: Mapped[int | None]
    row_start: Mapped[int | None]
    row_end: Mapped[int | None]
    column_headers: Mapped[list[str] | None]
```

**Conversations Model:**
```python
class ConversationORM(Base):
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    workspace_id: Mapped[str]
    user_id: Mapped[str]
    title: Mapped[str]
    provider: Mapped[str]  # anthropic, openai, ollama
    model: Mapped[str]
    system_prompt: Mapped[str | None]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    
    # Relations
    messages: Mapped[list[MessageORM]] = relationship(back_populates="conversation")
```

**Message Model:**
```python
class MessageORM(Base):
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    conversation_id: Mapped[str]
    role: Mapped[str]      # user, assistant, system
    content: Mapped[str]
    citations: Mapped[list[dict] | None]
    created_at: Mapped[datetime]
    
    # Relations
    conversation: Mapped[ConversationORM] = relationship(back_populates="messages")
```

---

### 7. **infrastructure/** - Adapters & External Services

**Chức năng:**
- Implement concrete implementations của ports
- Connect đến external services

```
infrastructure/
├── llm/
│   ├── registry.py              # LLM adapter registry
│   └── echo.py                  # Echo adapter (testing)
├── parsers/
│   ├── local_parser.py          # PDF/DOCX/XLSX parser
│   └── models.py                # ParsedDocument model
├── storage/
│   └── database_store.py        # Postgres blob storage
├── vector/
│   └── token_vector_backend.py  # Token embedding backend
├── graph/
│   └── neo4j_adapter.py         # Neo4j adapter
└── ontology/
    └── extractor.py             # Ontology extraction
```

#### **7.1 parsers/local_parser.py - Document Parsing**

**Hỗ trợ:**
- PDF: `pypdf.PdfReader`
- DOCX: `python-docx`
- XLSX: `openpyxl`

**Flow:**

```python
def parse_document(filename: str, content: bytes, title: str | None = None) -> ParsedDocument:
    """Main entry point để parse document"""
    document_type = Path(filename).suffix.lower().lstrip(".")
    
    if document_type == "pdf":
        return _parse_pdf(filename, content, title)
    elif document_type == "docx":
        return _parse_docx(filename, content, title)
    elif document_type == "xlsx":
        return _parse_xlsx(filename, content, title)
    else:
        raise UnsupportedDocumentTypeError(f"Type {document_type} not supported")
```

**PDF Parsing:**
```python
def _parse_pdf(filename: str, content: bytes, title: str | None) -> ParsedDocument:
    """Parse PDF file"""
    reader = PdfReader(BytesIO(content))
    chunks = []
    
    # Iterate mỗi page
    for page_index, page in enumerate(reader.pages, start=1):
        # Extract text từ page
        extracted = _normalize_block_text(page.extract_text() or "")
        if not extracted:
            continue
        
        # Extract first line as section title
        lines = [line.strip() for line in extracted.splitlines() if line.strip()]
        section_title = lines[0] if lines else None
        
        # Tạo chunk
        chunks.append(
            ParsedChunk(
                text=extracted,
                chunk_index=len(chunks),
                page_number=page_index,
                section_title=section_title
            )
        )
    
    if not chunks:
        raise ValueError(f"No extractable text in {filename}")
    
    return ParsedDocument(
        document_type="pdf",
        title=title or Path(filename).stem,
        chunks=chunks,
        parser_version=PARSER_VERSION,
    )
```

**DOCX Parsing:**
```python
def _parse_docx(filename: str, content: bytes, title: str | None) -> ParsedDocument:
    """Parse DOCX file - respects heading hierarchy"""
    document = DocxDocument(BytesIO(content))
    chunks = []
    heading_stack = []  # Theo dõi hierarchy
    paragraph_buffer = []
    
    def flush_paragraphs():
        """Tạo chunk từ buffered paragraphs"""
        if not paragraph_buffer:
            return
        heading_path = " > ".join(heading_stack) if heading_stack else "Document"
        chunks.append(
            ParsedChunk(
                text="\n".join(paragraph_buffer),
                chunk_index=len(chunks),
                section_title=heading_stack[-1] if heading_stack else "Document",
                heading_path=heading_path
            )
        )
        paragraph_buffer.clear()
    
    # Process từng paragraph
    for paragraph in document.paragraphs:
        text = _normalize_inline_text(paragraph.text)
        if not text:
            continue
        
        # Check nếu là heading
        style_name = paragraph.style.name if paragraph.style else ""
        if style_name.startswith("Heading"):
            flush_paragraphs()
            # Update heading stack
            level = _extract_heading_level(style_name)  # 1, 2, 3, etc
            heading_stack[:] = heading_stack[:level - 1]  # Remove deeper levels
            heading_stack.append(text)
            continue
        
        # Buffer paragraph
        paragraph_buffer.append(text)
    
    flush_paragraphs()
    
    # Process tables
    for table_index, table in enumerate(document.tables, start=1):
        rows = []
        for row in table.rows:
            cells = [_normalize_inline_text(cell.text) for cell in row.cells]
            cells = [cell for cell in cells if cell]
            rows.append(" | ".join(cells))
        # ... create table chunk
    
    return ParsedDocument(
        document_type="docx",
        title=title or Path(filename).stem,
        chunks=chunks,
        parser_version=PARSER_VERSION
    )
```

**XLSX Parsing:**
```python
def _parse_xlsx(filename: str, content: bytes, title: str | None) -> ParsedDocument:
    """Parse XLSX file - mỗi sheet xử lý riêng"""
    workbook = load_workbook(BytesIO(content))
    chunks = []
    
    # Process mỗi sheet
    for sheet in workbook.sheetnames:
        sheet_obj = workbook[sheet]
        # ... extract rows/data
        # Tạo chunks từ sheet data
    
    return ParsedDocument(
        document_type="xlsx",
        title=title or Path(filename).stem,
        chunks=chunks,
        parser_version=PARSER_VERSION
    )
```

#### **7.2 llm/registry.py - LLM Adapter Registry**

**Chức năng:**
- Registry các LLM adapters
- Resolve provider → adapter instance

```python
class AdapterRegistry:
    """Quản lý LLM adapters"""
    
    def __init__(self):
        self._adapters: dict[str, LLMAdapter] = {}
    
    def register(self, provider: str, adapter: LLMAdapter) -> None:
        """Đăng ký adapter cho provider"""
        self._adapters[provider] = adapter
    
    def get(self, provider: str) -> LLMAdapter | None:
        """Lấy adapter theo provider"""
        return self._adapters.get(provider)
    
    def list_providers(self) -> list[str]:
        """Liệt kê tất cả providers"""
        return list(self._adapters.keys())
```

#### **7.3 vector/token_vector_backend.py - Token Embedding**

```python
class TokenVectorBackend(VectorBackendPort):
    """Token-based vector embedding"""
    
    def embed_text(self, text: str) -> dict[str, int]:
        """Tính embedding từ text"""
        # Tokenize text
        tokens = text.split()
        embedding = {}
        
        # Tạo token frequency map
        for token in tokens:
            embedding[token] = embedding.get(token, 0) + 1
        
        return embedding
    
    def cosine_similarity(
        self,
        vec1: dict[str, int],
        vec2: dict[str, int]
    ) -> float:
        """Tính cosine similarity giữa 2 vectors"""
        # Lấy tất cả tokens
        all_tokens = set(vec1.keys()) | set(vec2.keys())
        
        # Calculate dot product
        dot_product = sum(
            vec1.get(token, 0) * vec2.get(token, 0)
            for token in all_tokens
        )
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        
        # Return similarity (-1 to 1)
        if mag1 == 0 or mag2 == 0:
            return 0
        
        return dot_product / (mag1 * mag2)
```

---

### 8. **ports/** - Port Interfaces (Abstraction)

**Chức năng:**
- Define contracts/interfaces
- Enable dependency injection
- Allow multiple implementations

```
ports/
├── graph_store.py               # Graph store interface
├── llm_adapter.py               # LLM adapter interface
├── object_store.py              # Blob storage interface
├── ontology_extractor.py        # Ontology extraction
├── parser.py                    # Document parser
├── secret_repo.py               # Secret/API key storage
├── task_model_resolver.py       # Task model selection
└── vector_backend.py            # Vector search backend
```

**Ví dụ - ObjectStorePort:**
```python
class ObjectStorePort(ABC):
    """Port cho object/blob storage"""
    
    @abstractmethod
    def put_document_binary(self, document_id: str, content: bytes) -> bytes | None:
        """Lưu binary content"""
        ...
    
    @abstractmethod
    def get_document_binary(self, document_id: str) -> bytes:
        """Lấy binary content"""
        ...
```

**Ví dụ - VectorBackendPort:**
```python
class VectorBackendPort(ABC):
    """Port cho vector embedding & search"""
    
    @abstractmethod
    def embed_text(self, text: str) -> dict[str, int]:
        """Tính embedding"""
        ...
    
    @abstractmethod
    def cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """Tính similarity"""
        ...
```

---

### 9. **schemas/** - Request/Response Models

**Chức năng:**
- Define API contract
- Validation với Pydantic

```
schemas/
├── agents.py                    # Agent DTOs
├── agent_profiles.py           # Agent profile DTOs
├── auth.py                      # Auth DTOs
├── chat.py                      # Chat DTOs
├── documents.py                # Document DTOs
├── ontology.py                 # Ontology DTOs
└── retrieval.py                # Retrieval DTOs
```

**Ví dụ - chat.py:**
```python
class SendMessageRequest(BaseModel):
    """Request để send message"""
    conversation_id: str
    content: str
    provider: str | None = None
    model: str | None = None
    use_retrieval: bool = False
    workspace_id: str | None = None
    document_ids: list[str] | None = None
    top_k: int = 3

class ChatReply(BaseModel):
    """Response của send_message"""
    conversation: ConversationResponse
    reply: MessageResponse
    citations: list[Citation]

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: list[Citation] | None
    created_at: datetime
```

**Ví dụ - documents.py:**
```python
class DocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    workspace_id: str
    document_type: str
    status: str
    chunk_count: int
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    error_message: str | None

class DocumentJobResponse(BaseModel):
    id: str
    document_id: str
    job_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
```

---

### 10. **workers/** - Asynchronous Task Processing

**Chức năng:**
- Queue async tasks với Celery
- Process documents, build ontology, etc

```
workers/
├── celery_app.py                # Celery app initialization
├── task_dispatcher.py           # TaskDispatcher (queue tasks)
└── worker_tasks.py              # Actual task implementations
```

#### **10.1 celery_app.py - Celery Configuration**

```python
# Khởi tạo Celery app
celery_app = Celery(
    "semantic_reasoning_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)

# Set eager mode nếu testing
if settings.celery_task_always_eager:
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = settings.celery_task_eager_propagates
```

#### **10.2 task_dispatcher.py - TaskDispatcher**

```python
class TaskDispatcher:
    """Enqueue async tasks"""
    
    def enqueue_document_processing(self, document_id: str) -> None:
        """Queue document processing pipeline"""
        from semantic_reasoning_agent.workers.worker_tasks import (
            process_document_task
        )
        # Gọi async task
        process_document_task.delay(document_id)
    
    def enqueue_ontology_build_processing(self, build_id: str) -> None:
        """Queue ontology build"""
        from semantic_reasoning_agent.workers.worker_tasks import (
            process_ontology_build_task
        )
        process_ontology_build_task.delay(build_id)
```

#### **10.3 worker_tasks.py - Task Implementations**

```python
@celery_app.task
def process_document_task(document_id: str) -> None:
    """Chính task pipeline"""
    # 1. Parse document
    # 2. Build chunks
    # 3. Embed chunks
    # 4. Upsert to vector store

@celery_app.task
def process_ontology_build_task(build_id: str) -> None:
    """Build ontology từ documents"""
    # 1. Load document chunks
    # 2. Extract entities & relations
    # 3. Canonicalize
    # 4. Save candidates
    # 5. Optionally sync to Neo4j
```

---

### 11. **tools/** - Execution Tools

**Chức năng:**
- Atomic execution units
- Implement Tool interface
- Used by workflows

```
tools/
├── base.py                      # Tool base class
└── ontology/                    # Ontology tools
    ├── extraction_tool.py
    └── validation_tool.py
```

**Tool Interface:**
```python
class Tool(ABC):
    """Base class cho tất cả tools"""
    
    tool_id: str
    
    @abstractmethod
    def run(self, envelope: ToolEnvelope) -> ToolResult:
        """Thực thi tool"""
        ...

@dataclass(frozen=True)
class ToolEnvelope:
    """Input wrapper cho tool"""
    tool_id: str
    inputs: Mapping[str, Any]
    workflow_run_id: UUID | None = None
    workspace_id: UUID | None = None
    timeout_s: float = 60.0
    metadata: Mapping[str, Any] = {}

@dataclass(frozen=True)
class ToolResult:
    """Output wrapper từ tool"""
    tool_id: str
    status: str  # "ok", "error", "skipped"
    outputs: Mapping[str, Any]
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: int = 0
```

---

### 12. **domain/** - Domain Models & Contracts

**Chức năng:**
- Domain-specific models
- Business contracts
- Error definitions

```
domain/
├── contracts/
│   ├── tool_envelope.py        # Tool I/O contracts
│   ├── evidence.py             # Evidence model
│   ├── ontology_context.py     # Ontology context
│   └── parsed_document.py      # Parsed document
├── ontology/
│   ├── entity.py               # Entity domain model
│   ├── relation.py             # Relation domain model
│   └── schema.py               # Schema domain model
└── errors.py                   # Domain exceptions
```

**Domain Errors:**
```python
class DomainError(Exception):
    """Base domain error"""

class ToolError(DomainError):
    """Tool execution failed"""

class ExtractionError(DomainError):
    """Extraction (parsing, ontology) failed"""

class WorkflowError(DomainError):
    """Workflow step failed"""
```

---

## ⚙️ Luồng Xử Lý Chính

### **Luồng 1: Send Chat Message**

```
User sends message via API
        ↓
POST /api/v1/chat/messages (SendMessageRequest)
        ↓
send_message() → ChatStreamService
        ↓
1. Get conversation
2. Validate provider/model ready
3. Get LLM adapter
4. Save user message
5. Generate LLM reply via adapter
6. If use_retrieval=true:
   - Embed query
   - Search similar chunks
   - Build citations
   - Compose grounded reply
7. Save assistant message
        ↓
Return ChatReply (conversation + message + citations)
```

### **Luồng 2: Upload Document**

```
User uploads file via API
        ↓
POST /api/v1/documents/upload (file)
        ↓
upload_document() → DocumentService
        ↓
1. Validate file type
2. Generate document_id
3. Save binary to object store
4. Create DocumentORM + JobORM records
5. Queue process_document_task
        ↓
Return DocumentResponse (status=uploaded)
```

### **Luồng 3: Process Document (Async Worker)**

```
process_document_task spawned by Celery
        ↓
Job 1: parse_document
  └─ Parse PDF/DOCX/XLSX
  └─ Extract text → chunks
  └─ Update DocumentORM status
  └─ Save ParsedDocument
        ↓
Job 2: build_chunks
  └─ Take parsed chunks
  └─ Generate chunk_id for each
  └─ Prepare IndexedChunks
  └─ Update job status
        ↓
Job 3: embed_chunks
  └─ For each chunk: embed_text()
  └─ Generate token embeddings
  └─ Update job status
        ↓
Job 4: upsert_qdrant
  └─ Save IndexedChunks to DB
  └─ Update document status=ready
  └─ Update chunk_count
        ↓
Complete!
```

### **Luồng 4: Search Documents**

```
User searches via API
        ↓
POST /api/v1/retrieval/search (query)
        ↓
search() → RetrievalService
        ↓
1. Embed query text
2. Load all chunks from workspace
3. Calculate cosine_similarity(query, each chunk)
4. Sort by score, take top_k
5. Build Citation for each result
        ↓
Return RetrievalSearchResponse (results with citations)
```

---

## 📡 API Endpoints

### **Chat API**

```
POST /api/v1/chat/messages
  Request:
    - conversation_id: string
    - content: string
    - provider: string (optional)
    - model: string (optional)
    - use_retrieval: boolean (default: false)
    - top_k: integer (default: 3)
  Response:
    - conversation: ConversationResponse
    - reply: MessageResponse
    - citations: Citation[]
```

### **Documents API**

```
POST /api/v1/documents/upload
  Request: multipart form
    - file: binary
    - title: string (optional)
    - workspace_id: string (optional)
    - tags: comma-separated (optional)
  Response: DocumentResponse

GET /api/v1/documents
  Response: DocumentResponse[]

GET /api/v1/documents/{document_id}
  Response: DocumentResponse

GET /api/v1/documents/{document_id}/jobs
  Response: DocumentJobResponse[]

POST /api/v1/documents/{document_id}/reprocess
  Response: DocumentReprocessResponse
```

### **Retrieval API**

```
POST /api/v1/retrieval/search
  Request:
    - query: string
    - workspace_id: string (optional)
    - document_ids: string[] (optional)
    - top_k: integer (default: 3)
  Response: RetrievalSearchResponse
    - query: string
    - results: RetrievalResult[]
      - chunk_id, document_id, document_title
      - score, excerpt, citation
```

### **Ontology API**

```
POST /api/v1/ontology/builds
  Request: OntologyBuildRequest
  Response: OntologyBuildResponse

GET /api/v1/ontology/builds
  Response: OntologyBuildResponse[]

GET /api/v1/ontology/builds/{build_id}
  Response: OntologyBuildResponse

GET /api/v1/ontology/builds/{build_id}/entities
  Response: OntologyEntityResponse[]

POST /api/v1/ontology/builds/{build_id}/publish
  Response: OntologyBuildResponse
```

---

## 🛠️ Công Nghệ Sử Dụng

| Lớp | Công Nghệ | Vai Trò |
|-----|-----------|--------|
| **Framework** | FastAPI | Async web framework |
| **Server** | Uvicorn | ASGI server |
| **Database** | PostgreSQL | Primary data store |
| **ORM** | SQLAlchemy | Database abstraction |
| **Queue** | Celery | Async task processing |
| **Broker** | Redis | Message broker + cache |
| **Graph DB** | Neo4j | Knowledge graph (optional) |
| **File Parsing** | pypdf, python-docx, openpyxl | Document extraction |
| **Validation** | Pydantic | Request/response validation |
| **LLM** | Anthropic, OpenAI, Google, Ollama | Language models |
| **Migrations** | Alembic | Schema versioning |

---

## 📝 File Configuration

### **.env - Environment Variables**

```env
# App
APP_ENV=development
APP_NAME=Semantic Reasoning Agent

# Database
DATABASE_URL=postgresql+psycopg://semantic:semantic@localhost:5432/semantic_reasoning

# Cache & Queue
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Neo4j (optional)
NEO4J_ENABLED=false
NEO4J_URI=bolt://localhost:7687

# Default workspace
DEFAULT_WORKSPACE_ID=workspace-demo

# LLM
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
ONTOLOGY_LLM_PROVIDER=anthropic
```

### **pyproject.toml - Dependencies**

```toml
[project]
dependencies = [
    "fastapi~=0.100.0",
    "sqlalchemy~=2.0.0",
    "celery~=5.3.0",
    "redis~=5.0.0",
    "pydantic-settings~=2.0.0",
    "pypdf~=3.17.0",
    "python-docx~=0.8.11",
    "openpyxl~=3.11.0",
    "neo4j~=5.14.0",
]
```

---

## 🚀 Khởi Động

### **1. Start API Server**
```bash
python serve.py
# Hoặc
uvicorn semantic_reasoning_agent.main:app --reload
```

### **2. Start Celery Worker**
```bash
celery -A semantic_reasoning_agent.workers.celery_app worker --loglevel=info
```

### **3. Start Redis** (nếu chưa có)
```bash
redis-server
```

### **4. Start PostgreSQL** (nếu chưa có)
```bash
psql -U semantic
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      USER/CLIENT                            │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼──────┐
    │ Chat API │          │ Document API
    └────┬─────┘          └─────┬──────┘
         │                      │
    ┌────▼────────────┐  ┌──────▼──────────┐
    │ ChatStreamSvc   │  │ DocumentService │
    └────┬────────────┘  └──────┬──────────┘
         │                      │
    ┌────▼──────────┐  ┌───────▼────────┐
    │ LLM Adapter   │  │ TaskDispatcher  │
    │ Retrieval     │  │ (Celery)        │
    └────┬──────────┘  └───────┬────────┘
         │                     │
    ┌────▼──────────────────────▼─┐
    │    PostgreSQL Database       │
    │  (documents, chunks, etc)    │
    └──────────────────────────────┘
         │
    ┌────▼──────────┐    ┌──────────────┐
    │ Redis Queue   │    │ Neo4j (opt)  │
    │ Celery Tasks  │    │ Knowledge G  │
    └───────────────┘    └──────────────┘
```

---

## 🔄 Workflow Summary

| Workflow | Trigger | Steps | Output |
|----------|---------|-------|--------|
| **Chat** | User message | 1. Validate 2. Get LLM 3. Generate reply 4. Optional retrieval 5. Return | ChatReply + Citations |
| **Document Ingestion** | Upload file | 1. Parse 2. Chunk 3. Embed 4. Index | Ready document |
| **Search** | Search query | 1. Embed query 2. Find similar 3. Rank | Top-k results + Citations |
| **Ontology Build** | Manual trigger | 1. Extract entities 2. Extract relations 3. Canonicalize 4. Review | OntologyBuild |

---

**Document Version: 1.0**  
**Last Updated: 2026-04-19**  
**Backend Framework: FastAPI 0.100+**
