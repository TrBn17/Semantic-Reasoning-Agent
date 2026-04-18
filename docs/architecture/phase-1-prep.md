# Phase 1 Preparation Notes

## Goal

Prepare the repository for `Phase 1 - Chat Core & Multi-LLM` without pretending the full feature set already exists.

## Decisions in this pass

- Start backend-first with FastAPI because the current repo had no reusable application structure.
- Keep provider integrations behind adapter interfaces so Anthropic, OpenAI, Gemini, and Ollama can be added without reshaping the API layer.
- Use an in-memory conversation service temporarily to prove API contracts before adding Postgres.
- Expose model readiness explicitly so unsupported providers fail clearly instead of silently falling back.

## Boundaries

This pass does not implement:

- persistent storage
- streaming transport
- real provider SDK calls
- Langfuse tracing
- frontend pages
- worker jobs

## Immediate next steps

1. Add SQLAlchemy models and migrations for conversations and messages.
2. Add SSE or websocket streaming for assistant replies.
3. Implement provider adapters behind the current registry.
4. Add request tracing and token usage capture.
