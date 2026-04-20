from __future__ import annotations

from sqlalchemy import select

from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.ontology import (
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
