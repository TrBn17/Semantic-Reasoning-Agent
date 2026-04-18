from celery import Celery

from semantic_reasoning_agent.config import get_settings


settings = get_settings()

celery_app = Celery(
    "semantic_reasoning_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["semantic_reasoning_agent.worker_tasks"],
)

celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
