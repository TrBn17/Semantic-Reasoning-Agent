# Persistence ORM Audit

Scope: `apps/backend/src/semantic_reasoning_agent/persistence/models`

Baseline status: `20260422_baseline` is the single Alembic revision for fresh databases. The audit below classifies each ORM model against four checks:

- present in `Base.metadata`
- present in the Alembic baseline
- has an active caller in service/repository/entrypoint code
- has test or API surface evidence

## Keep

| Model | Evidence |
| --- | --- |
| `ConversationORM` | Used by `services/conversation_service.py`; exercised by `tests/test_api.py`. |
| `MessageORM` | Used by `services/conversation_service.py`; exercised by chat API tests. |
| `DocumentORM` | Central document record in `documents/service.py`; covered by upload/reprocess tests. |
| `DocumentJobORM` | Used by `documents/service.py`; surfaced by document jobs API/tests. |
| `DocumentChunkORM` | Used by `documents/service.py`, `services/retrieval_service.py`, and `retrieval.internal`; covered by retrieval tests. |
| `DocumentArtifactORM` | Used by `documents/service.py`; surfaced by document artifact reads. |
| `DocumentExtractionRunORM` | Used by `documents/service.py`; returned by extraction-run API surface. |
| `OntologyBuildORM` | Used throughout `services/ontology_service.py`; covered by ontology build/publish tests. |
| `OntologyBuildStepORM` | Used by `services/ontology_service.py` for step tracking; exposed in build responses/tests. |
| `OntologyCandidateEntityORM` | Used by `services/ontology_service.py`; covered by review flows. |
| `OntologyCandidateRelationORM` | Used by `services/ontology_service.py`; covered by review flows. |
| `OntologyVersionORM` | Used by `services/ontology_service.py` and graph publication. |
| `OntologyEntityTypeDefinitionORM` | Used by `services/ontology_service.py`; surfaced in graph/version responses. |
| `OntologyRelationTypeDefinitionORM` | Used by `services/ontology_service.py`; surfaced in graph/version responses. |
| `OntologyEntityORM` | Used by `services/ontology_service.py` and `tools/ontology/lookup_tool.py`. |
| `OntologyRelationORM` | Used by `services/ontology_service.py` and `tools/ontology/lookup_tool.py`. |
| `OntologyGraphDraftORM` | Used directly by draft/edit/publish flows in `services/ontology_service.py`. |
| `AgentProfileORM` | Used by `services/agent_profile_service.py` and `services/conversation_service.py`; covered by `tests/test_agent_capabilities_api.py`. |
| `KnowledgePackORM` | Used by `services/knowledge_pack_service.py`; exposed by `/api/v1/knowledge-packs`. |
| `KnowledgePackDocumentORM` | Used by `services/knowledge_pack_service.py`; covered by knowledge-pack CRUD tests. |
| `ProviderConfigORM` | Used by `services/model_config_service.py` and auth workspace discovery query. |
| `ProviderSecretORM` | Used by `services/secret_service.py` and settings update flow. |
| `TaskModelConfigORM` | Used by `services/model_config_service.py` for workspace task assignments. |
| `TaskRunORM` | Persisted by `services/runtime_audit_service.py`; exercised by task runtime API/tests. |
| `TaskRunStepORM` | Persisted by `services/runtime_audit_service.py`; tied to runtime trace audit. |
| `ToolCallAuditORM` | Persisted by `services/runtime_audit_service.py`; reflected in task runtime traces. |
| `EvidenceBundleORM` | Persisted by `services/runtime_audit_service.py`; part of runtime audit persistence. |
| `EvidenceConflictORM` | Persisted by `services/runtime_audit_service.py`; populated when conflicts are recorded. |
| `OutputRouteORM` | Persisted by `services/runtime_audit_service.py`; records final output routing. |

## Keep But Missing Relationship / Index / Constraint Cleanup

| Model | Cleanup gap |
| --- | --- |
| `ConversationORM` | `agent_profile_id` is indexed but has no FK/relationship to `agent_profiles`; current services resolve it manually. |
| `AgentProfileTaskModelORM` | Upsert logic in `services/agent_profile_service.py` expects one row per `(agent_profile_id, task_type)` but the table has no unique constraint. |
| `ProviderConfigORM` | Workspace/provider upsert path expects uniqueness on `(workspace_id, provider)` but that constraint is not enforced at the DB layer. |
| `ProviderSecretORM` | Repository semantics assume uniqueness on `(workspace_id, provider, field_key)`; today that is enforced only by the synthesized `id`. |
| `TaskModelConfigORM` | Workspace/task assignment upsert path expects uniqueness on `(workspace_id, task_type)` but the DB does not enforce it directly. |
| `OntologyBuildORM` | `published_version_id` is a loose string reference, not a foreign key to `ontology_versions`. |

## Unused But Intentional Placeholder

None in the current ORM set.

## Candidate For Removal

None in the current ORM set.
