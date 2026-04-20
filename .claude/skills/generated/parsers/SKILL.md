---
name: parsers
description: "Skill for the Parsers area of Semantic-Reasoning-Agent. 11 symbols across 2 files."
---

# Parsers

11 symbols | 2 files | Cohesion: 91%

## When to Use

- Working with code in `apps/`
- Understanding how parse_document, flush_paragraphs, ParsedChunk work
- Modifying parsers-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | UnsupportedDocumentTypeError, parse_document, _parse_pdf, _parse_docx, flush_paragraphs (+4) |
| `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/models.py` | ParsedChunk, ParsedDocument |

## Entry Points

Start here when exploring this area:

- **`parse_document`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py:18`
- **`flush_paragraphs`** (Function) — `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py:66`
- **`ParsedChunk`** (Class) — `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/models.py:9`
- **`ParsedDocument`** (Class) — `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/models.py:24`
- **`UnsupportedDocumentTypeError`** (Class) — `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py:14`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `ParsedChunk` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/models.py` | 9 |
| `ParsedDocument` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/models.py` | 24 |
| `UnsupportedDocumentTypeError` | Class | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 14 |
| `parse_document` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 18 |
| `flush_paragraphs` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 66 |
| `_parse_pdf` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 31 |
| `_parse_docx` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 60 |
| `_parse_xlsx` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 126 |
| `_normalize_block_text` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 201 |
| `_normalize_inline_text` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 206 |
| `_stringify_cell` | Function | `apps/backend/src/semantic_reasoning_agent/infrastructure/parsers/local_parser.py` | 217 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Process_document → _normalize_block_text` | cross_community | 4 |
| `Process_document → ParsedChunk` | cross_community | 4 |
| `Process_document → ParsedDocument` | cross_community | 4 |
| `Upload_documents → UnsupportedDocumentTypeError` | cross_community | 4 |
| `Process_document → UnsupportedDocumentTypeError` | cross_community | 3 |
| `Ingest_files_and_publish → UnsupportedDocumentTypeError` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Services | 1 calls |

## How to Explore

1. `gitnexus_context({name: "parse_document"})` — see callers and callees
2. `gitnexus_query({query: "parsers"})` — find related execution flows
3. Read key files listed above for implementation details
