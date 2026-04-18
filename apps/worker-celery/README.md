# Worker Notes (Legacy Path)

The production-facing worker entrypoint is now `apps/backend/worker/serve.py`.
The Celery runtime package lives in `apps/backend/src/semantic_reasoning_agent`.

Legacy run command:

```powershell
.venv\Scripts\python.exe -m celery -A semantic_reasoning_agent.celery_app.celery_app worker --loglevel INFO --pool solo
```

This placeholder folder is kept so the repo still reflects the intended `/apps/worker-celery` shape from the BRD.
