"""CRUD for Graphiti ontology graph projections — one Neo4j ``group_id`` per projection (scoped by knowledge pack)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from semantic_reasoning_agent.infrastructure.graphiti.graphiti_group_id import (
    graphiti_group_id_for_projection,
)
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models import KnowledgePackORM, OntologyGraphProjectionORM
from semantic_reasoning_agent.schemas.ontology import (
    OntologyGraphProjectionCreateRequest,
    OntologyGraphProjectionResponse,
)


class OntologyGraphProjectionNotFoundError(LookupError):
    """Projection id missing."""


class OntologyGraphProjectionError(ValueError):
    """Invalid projection operation."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OntologyGraphProjectionService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        graphiti_gateway: GraphitiGateway,
    ) -> None:
        self._database_manager = database_manager
        self._graphiti_gateway = graphiti_gateway

    def list_projections(self, workspace_id: str) -> list[OntologyGraphProjectionResponse]:
        with self._database_manager.session() as session:
            rows = session.scalars(
                select(OntologyGraphProjectionORM)
                .where(OntologyGraphProjectionORM.workspace_id == workspace_id)
                .order_by(OntologyGraphProjectionORM.created_at.desc())
            ).all()
            return [
                self._to_response(workspace_id=r.workspace_id, row=r)
                for r in rows
            ]

    def create_projection(
        self,
        payload: OntologyGraphProjectionCreateRequest,
    ) -> OntologyGraphProjectionResponse:
        proj_id = str(uuid4())
        now = utc_now()
        ws = payload.workspace_id.strip()
        kp_id = payload.knowledge_pack_id.strip()
        name = payload.name.strip()
        if not name:
            raise OntologyGraphProjectionError("projection name cannot be empty.")
        with self._database_manager.session() as session:
            kp = session.get(KnowledgePackORM, kp_id)
            if kp is None:
                raise OntologyGraphProjectionError(f"Knowledge pack '{kp_id}' was not found.")
            if kp.workspace_id != ws:
                raise OntologyGraphProjectionError(
                    "Knowledge pack does not belong to the given workspace."
                )
            row = OntologyGraphProjectionORM(
                id=proj_id,
                workspace_id=ws,
                knowledge_pack_id=kp_id,
                name=name,
                created_at=now,
            )
            session.add(row)
            try:
                session.flush()
            except IntegrityError as exc:
                raise OntologyGraphProjectionError(
                    "A graph with this name already exists for this knowledge pack."
                ) from exc
        with self._database_manager.session() as session:
            row = session.get(OntologyGraphProjectionORM, proj_id)
            assert row is not None
            return self._to_response(workspace_id=ws, row=row)

    def delete_projection(self, projection_id: str) -> None:
        with self._database_manager.session() as session:
            row = session.get(OntologyGraphProjectionORM, projection_id)
            if row is None:
                raise OntologyGraphProjectionNotFoundError(
                    f"Ontology graph projection '{projection_id}' was not found."
                )
            ws = row.workspace_id
            gid = graphiti_group_id_for_projection(ws, row.id)
        self._graphiti_gateway.delete_group_data(group_id=gid)
        with self._database_manager.session() as session:
            row2 = session.get(OntologyGraphProjectionORM, projection_id)
            if row2 is not None:
                session.delete(row2)

    def resolve_graphiti_group_id_for_publish(
        self,
        workspace_id: str,
        ontology_graph_projection_id: str | None,
    ) -> str | None:
        """Return Graphiti ``group_id`` string, or ``None`` to use legacy workspace-only partition."""
        if not ontology_graph_projection_id or not ontology_graph_projection_id.strip():
            return None
        pid = ontology_graph_projection_id.strip()
        with self._database_manager.session() as session:
            row = session.get(OntologyGraphProjectionORM, pid)
            if row is None:
                raise OntologyGraphProjectionError(
                    f"Ontology graph projection '{pid}' was not found."
                )
            if row.workspace_id != workspace_id:
                raise OntologyGraphProjectionError(
                    "Ontology graph projection does not belong to this workspace."
                )
        return graphiti_group_id_for_projection(workspace_id, pid)

    @staticmethod
    def _to_response(*, workspace_id: str, row: OntologyGraphProjectionORM) -> OntologyGraphProjectionResponse:
        return OntologyGraphProjectionResponse(
            id=row.id,
            workspace_id=workspace_id,
            knowledge_pack_id=row.knowledge_pack_id,
            name=row.name,
            graphiti_group_id=graphiti_group_id_for_projection(workspace_id, row.id),
            created_at=row.created_at,
        )

    def projection_group_ids_for_search(
        self,
        *,
        workspace_id: str,
        projection_row_ids: list[str],
    ) -> list[str]:
        ids = []
        lookup = [p.strip() for p in projection_row_ids if p.strip()]
        if not lookup:
            return [workspace_id]
        with self._database_manager.session() as session:
            for pid in lookup:
                row = session.get(OntologyGraphProjectionORM, pid)
                if row is None or row.workspace_id != workspace_id:
                    raise OntologyGraphProjectionError(f"Unknown graph projection id '{pid}'.")
                ids.append(graphiti_group_id_for_projection(workspace_id, row.id))
        return ids
