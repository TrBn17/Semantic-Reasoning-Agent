# Backend (FastAPI + Celery worker entrypoints)

- **Python package:** `apps/backend/src/semantic_reasoning_agent`
- **Tests:** `apps/backend/tests`
- **API:** `python apps/backend/serve.py` (hoặc `uvicorn` với `app_dir=apps/backend/src`)
- **Worker:** `python apps/backend/worker/serve.py`

Celery tasks import cùng package từ `apps/backend/src`.
