class TaskDispatcher:
    def enqueue_document_processing(self, document_id: str) -> None:
        from semantic_reasoning_agent.worker_tasks import process_document_task

        process_document_task.delay(document_id)

    def enqueue_ontology_build_processing(self, build_id: str) -> None:
        from semantic_reasoning_agent.worker_tasks import process_ontology_build_task

        process_ontology_build_task.delay(build_id)
