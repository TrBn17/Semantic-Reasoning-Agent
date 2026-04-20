from __future__ import annotations

from sqlalchemy import select

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.documents import DocumentChunkORM, DocumentORM
from semantic_reasoning_agent.persistence.models.ontology import (
    OntologyArchitectureDraftORM,
    OntologyArchitectureEvidenceLinkORM,
    OntologyBuildORM,
    OntologyCandidateEntityORM,
    OntologyCandidateRelationORM,
)


class OntologyRepository:
    """Read-only helpers backing the OntologyService and the upcoming
    OntologySchemaRegistry (R3).

    The schema-registry methods return the descriptive set of entity/relation
    types observed across past builds for a workspace — fed to the LLM
    extractor as a prior, never as a constraint.
    """

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def get_build(self, build_id: str) -> OntologyBuildORM | None:
        with self._database_manager.session() as session:
            return session.get(OntologyBuildORM, build_id)

    def list_used_entity_types(self, workspace_id: str) -> list[str]:
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(OntologyCandidateEntityORM.entity_type)
                .where(OntologyCandidateEntityORM.workspace_id == workspace_id)
                .distinct()
            ).all()
            return sorted(filter(None, rows))

    def list_used_relation_types(self, workspace_id: str) -> list[str]:
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(OntologyCandidateRelationORM.relation_type)
                .where(OntologyCandidateRelationORM.workspace_id == workspace_id)
                .distinct()
            ).all()
            return sorted(filter(None, rows))

    def get_active_architecture_draft(
        self,
        workspace_id: str,
        domain: str | None = None,
    ) -> OntologyArchitectureDraftORM | None:
        with self._database_manager.session() as session:
            statement = (
                select(OntologyArchitectureDraftORM)
                .where(
                    OntologyArchitectureDraftORM.workspace_id == workspace_id,
                    OntologyArchitectureDraftORM.is_active.is_(True),
                    OntologyArchitectureDraftORM.status == "approved",
                )
                .order_by(OntologyArchitectureDraftORM.updated_at.desc())
            )
            drafts = session.scalars(statement).all()
            if domain:
                for draft in drafts:
                    if draft.domain == domain:
                        return draft
            return drafts[0] if drafts else None

    def list_architecture_entity_types(self, workspace_id: str) -> list[str]:
        draft = self.get_active_architecture_draft(workspace_id)
        if draft is None:
            return []
        values = [
            str(item.get("name", "")).strip()
            for item in draft.entity_types or []
            if isinstance(item, dict)
        ]
        return sorted({value for value in values if value})

    def list_architecture_relation_types(self, workspace_id: str) -> list[str]:
        draft = self.get_active_architecture_draft(workspace_id)
        if draft is None:
            return []
        values = [
            str(item.get("name", "")).strip()
            for item in draft.relation_types or []
            if isinstance(item, dict)
        ]
        return sorted({value for value in values if value})

    def get_document_chunk_samples(
        self,
        document_ids: list[str],
        *,
        limit: int = 8,
    ) -> list[tuple[str, str | None, str]]:
        if not document_ids:
            return []
        with self._database_manager.session() as session:
            rows = session.execute(
                select(DocumentChunkORM.chunk_id, DocumentChunkORM.document_id, DocumentChunkORM.text)
                .where(DocumentChunkORM.document_id.in_(document_ids))
                .order_by(DocumentChunkORM.document_id, DocumentChunkORM.chunk_index)
                .limit(limit)
            ).all()
            return [(str(chunk_id), str(document_id) if document_id else None, text) for chunk_id, document_id, text in rows]

    def get_document_workspace(self, document_id: str) -> str | None:
        with self._database_manager.session() as session:
            document = session.get(DocumentORM, document_id)
            if document is None:
                return None
            return document.workspace_id
