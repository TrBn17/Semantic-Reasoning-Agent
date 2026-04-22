# Phase 1 API Contract Draft

## Available now

- `GET /health`
- `GET /api/v1/auth/me`
- `GET /api/v1/settings/models`
- `GET /api/v1/conversations`
- `POST /api/v1/conversations`
- `GET /api/v1/conversations/{conversation_id}`
- `POST /api/v1/chat/messages`

## Purpose of the current contract

These endpoints establish the minimum backend seams needed for Phase 1 work:

- a user/workspace identity placeholder
- a model catalog
- conversation lifecycle endpoints
- a chat entrypoint with provider validation

## Planned upgrades

- switch `POST /api/v1/chat/messages` to streaming
- persist conversations and messages in Postgres
- add usage metrics and traces
- add model fallback policy
