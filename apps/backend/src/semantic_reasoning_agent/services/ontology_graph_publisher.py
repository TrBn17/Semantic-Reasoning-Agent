from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from semantic_reasoning_agent.domain.contracts.published_ontology_snapshot import PublishedOntologySnapshot
from semantic_reasoning_agent.infrastructure.graphiti.graphiti_gateway import GraphitiGateway
from semantic_reasoning_agent.schemas.ontology import OntologyEntityResponse

logger = logging.getLogger(__name__)

MAX_CHUNK_EPISODES = 5000


def _graphiti_group_id(snapshot: PublishedOntologySnapshot) -> str:
    return snapshot.graphiti_group_id or snapshot.workspace_id


@dataclass(slots=True)
class GraphitiDocumentChunk:
    chunk_id: str
    document_id: str
    document_title: str
    text: str
    created_at: datetime | None = None


class OntologyGraphPublisherError(RuntimeError):
    """Raised when the runtime graph cannot be prepared during publish."""


class OntologyGraphPublisher:
    def __init__(self, graphiti_gateway: GraphitiGateway) -> None:
        self._graphiti_gateway = graphiti_gateway
        self.last_published_snapshot: PublishedOntologySnapshot | None = None
        self._last_sync_workspace: str | None = None
        self._last_sync_ok: bool = False

    def graphiti_indexed_for(self, workspace_id: str) -> bool:
        return self._last_sync_ok and self._last_sync_workspace == workspace_id

    def is_enabled(self) -> bool:
        return self._graphiti_gateway.is_enabled()

    def publish(
        self,
        snapshot: PublishedOntologySnapshot | None = None,
        *,
        document_chunks: Sequence[GraphitiDocumentChunk] | None = None,
    ) -> None:
        if snapshot is not None:
            self.last_published_snapshot = snapshot
        if not self._graphiti_gateway.is_enabled():
            return
        try:
            self._graphiti_gateway.ensure_indices()
        except Exception as exc:  # noqa: BLE001
            raise OntologyGraphPublisherError(str(exc) or exc.__class__.__name__) from exc

        if snapshot is None:
            return

        any_ok = False
        try:
            any_ok = self._ingest_snapshot(snapshot, list(document_chunks or ()))
        except Exception:
            logger.exception("Graphiti ontology publish failed for workspace %s", snapshot.workspace_id)

        self._last_sync_ok = any_ok
        self._last_sync_workspace = snapshot.workspace_id if any_ok else None

    def _ingest_snapshot(
        self,
        snapshot: PublishedOntologySnapshot,
        chunks: list[GraphitiDocumentChunk],
    ) -> bool:
        """Best-effort Graphiti sync; returns True if at least one write succeeded."""
        any_ok = False
        entity_by_id: dict[str, OntologyEntityResponse] = {e.id: e for e in snapshot.entities}
        touched: set[str] = set()
        for relation in snapshot.relations:
            src = entity_by_id.get(relation.source_entity_id)
            tgt = entity_by_id.get(relation.target_entity_id)
            if src is None or tgt is None:
                logger.warning(
                    "Skipping relation %s — missing endpoint entity (src=%s tgt=%s)",
                    relation.id,
                    relation.source_entity_id,
                    relation.target_entity_id,
                )
                continue
            fact = (relation.evidence_text or "").strip() or (
                f"{src.name} {relation.relation_type} {tgt.name} (confidence {relation.confidence:.2f})"
            )
            try:
                self._graphiti_gateway.upsert_edge(
                    uuid=relation.id,
                    source_uuid=src.id,
                    target_uuid=tgt.id,
                    source_name=src.name,
                    target_name=tgt.name,
                    relation_type=relation.relation_type,
                    fact=fact,
                    valid_at=relation.created_at,
                    group_id=_graphiti_group_id(snapshot),
                    source_entity_type=src.entity_type,
                    target_entity_type=tgt.entity_type,
                )
                any_ok = True
                touched.add(src.id)
                touched.add(tgt.id)
            except Exception:
                logger.exception("Graphiti upsert_edge failed for relation %s", relation.id)

        for entity in snapshot.entities:
            if entity.id in touched:
                continue
            try:
                self._graphiti_gateway.upsert_node(
                    uuid=entity.id,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    aliases=list(entity.aliases or ()),
                    group_id=_graphiti_group_id(snapshot),
                    source_document_id=entity.source_document_id,
                )
                any_ok = True
            except Exception:
                logger.exception("Graphiti upsert_node failed for entity %s", entity.id)

        for index, chunk in enumerate(chunks[:MAX_CHUNK_EPISODES]):
            body = (chunk.text or "").strip()
            if not body:
                continue
            try:
                self._graphiti_gateway.ingest_episode(
                    name=f"ontology-doc-{chunk.document_id}",
                    episode_body=body[:120_000],
                    source_description=chunk.document_title or chunk.document_id,
                    group_id=_graphiti_group_id(snapshot),
                    reference_time=chunk.created_at,
                )
                any_ok = True
            except Exception:
                logger.exception(
                    "Graphiti ingest_episode failed for chunk %s (%s/%s)",
                    chunk.chunk_id,
                    index + 1,
                    min(len(chunks), MAX_CHUNK_EPISODES),
                )

        return any_ok
