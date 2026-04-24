import logging

from semantic_reasoning_agent.workers.celery_app import celery_app

# Neo4j emits many INFO notifications for IF NOT EXISTS schema calls.
# Keep worker logs focused on actionable warnings/errors.
logging.getLogger("neo4j.notifications").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)


@celery_app.task(name="semantic_reasoning_agent.tasks.process_document")
def process_document_task(document_id: str) -> str:
    from semantic_reasoning_agent.core.container import get_app_container

    get_app_container().document_service.process_document(document_id)
    return document_id


@celery_app.task(name="semantic_reasoning_agent.tasks.process_ontology_build")
def process_ontology_build_task(build_id: str) -> str:
    from semantic_reasoning_agent.core.container import get_app_container

    get_app_container().ontology_service.process_build(build_id)
    return build_id
