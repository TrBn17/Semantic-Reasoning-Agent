# Local Setup

## Infrastructure

```powershell
docker compose up -d postgres redis neo4j minio createbuckets
```

## Python setup

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev]
```

Optional extended document conversion stack:

```powershell
.venv\Scripts\python.exe -m pip install -e .[dev,document_conversion]
```

For full MarkItDown capability coverage (recommended for ontology ingestion in mixed document sets):

```powershell
.venv\Scripts\python.exe -m pip install "markitdown[all]"
```

`markitdown[all]` enables optional converters/extractors for:
- Office: `docx`, `pptx`, `xlsx`, `xls`, Outlook (`.msg`)
- Documents: `pdf`, `epub`, `html`, `csv/json/xml/txt`
- Media: image metadata/OCR patterns, audio transcription (`wav`, `mp3`)
- Integrations: Azure Document Intelligence, YouTube transcript support

## API

```powershell
.venv\Scripts\python.exe apps/backend/serve.py
```

## Worker

```powershell
.venv\Scripts\python.exe apps/backend/worker/serve.py
```

## Frontend

```powershell
cd apps/frontend
npm install
npm run dev
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest apps/backend/tests
```

## Supported Phase 2 starter formats

- `pdf`
- `docx`
- `xlsx`
- `csv`

Uploads accept `ingestion_mode=ontology|retrieval|both` (default `both`).

## Ontology extraction tuning (optional)

Add these env vars in `.env` when tuning extraction for large documents or reasoning models:

- `ONTOLOGY_PROMPT_VERSION=v2`
- `ONTOLOGY_EXTRACTION_MAX_TOKENS=8192`
- `ONTOLOGY_EXTRACTION_REASONING_EFFORT=low`
- `ONTOLOGY_EXTRACTION_MAX_CHUNKS=8`

## MinIO retention for extracted markdown

- Set `OBJECT_STORE_BACKEND=minio` to store document artifacts in MinIO.
- Local `docker-compose.yml` now applies an ILM rule on startup via `createbuckets`:
  - prefix: `documents/`
  - expiry: `${MINIO_MARKDOWN_RETENTION_DAYS:-30}` days
- To customize retention, define `MINIO_MARKDOWN_RETENTION_DAYS` in `.env` before running compose.
