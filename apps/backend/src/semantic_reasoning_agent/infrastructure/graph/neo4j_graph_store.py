from __future__ import annotations

import json
from datetime import datetime

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.ports.graph_store import (
    GraphStore,
    GraphStoreError,
    PublishedOntologySnapshot,
)
from semantic_reasoning_agent.schemas.ontology import (
    OntologyEntityResponse,
    OntologyGraphResponse,
    OntologyRelationResponse,
    OntologyVersionResponse,
)


class Neo4jGraphStore(GraphStore):
    def __init__(self, settings: Settings) -> None:
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise GraphStoreError(
                "Neo4j support requires the 'neo4j' package to be installed."
            ) from exc

        self._database = settings.neo4j_database
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def is_enabled(self) -> bool:
        return True

    def verify_connection(self) -> None:
        try:
            with self._driver.session(database=self._database) as session:
                session.run("RETURN 1 AS ok").single()
        except Exception as exc:
            raise GraphStoreError("Failed to connect to Neo4j.") from exc

    def sync_published_graph(self, snapshot: PublishedOntologySnapshot) -> None:
        parameters = {
            "workspace_id": snapshot.workspace_id,
            "version": _serialize_version(snapshot.version),
            "entities": [_serialize_entity(entity) for entity in snapshot.entities],
            "relations": [_serialize_relation(relation) for relation in snapshot.relations],
        }
        try:
            with self._driver.session(database=self._database) as session:
                session.execute_write(_replace_version_snapshot, parameters)
        except Exception as exc:
            raise GraphStoreError(
                f"Failed to sync ontology version '{snapshot.version.id}' to Neo4j."
            ) from exc

    def get_graph(self, workspace_id: str) -> OntologyGraphResponse:
        try:
            with self._driver.session(database=self._database) as session:
                version_record = session.run(
                    """
                    MATCH (version:OntologyVersion)
                    WHERE version.workspace_id = $workspace_id
                    RETURN version
                    ORDER BY version.version_number DESC
                    LIMIT 1
                    """,
                    workspace_id=workspace_id,
                ).single()
                if version_record is None:
                    return OntologyGraphResponse(workspace_id=workspace_id)

                version = _deserialize_version(version_record["version"])
                entity_records = session.run(
                    """
                    MATCH (ov:OntologyVersion)-[:HAS_ENTITY]->(entity:OntologyEntity)
                    WHERE ov.id = $version_id
                    RETURN entity
                    ORDER BY entity.name
                    """,
                    version_id=version.id,
                )
                relation_records = session.run(
                    """
                    MATCH (source:OntologyEntity)-[relation:ONTOLOGY_RELATION]->(target:OntologyEntity)
                    WHERE source.version_id = $version_id
                      AND relation.version_id = $version_id
                      AND target.version_id = $version_id
                    RETURN relation, source.id AS source_entity_id, target.id AS target_entity_id
                    ORDER BY relation.relation_type, source.name, target.name
                    """,
                    version_id=version.id,
                )
                entity_rows = [record["entity"] for record in entity_records]
                relation_rows = [
                    (
                        record["relation"],
                        record["source_entity_id"],
                        record["target_entity_id"],
                    )
                    for record in relation_records
                ]
        except Exception as exc:
            raise GraphStoreError(f"Failed to read the latest Neo4j graph for '{workspace_id}'.") from exc

        return OntologyGraphResponse(
            workspace_id=workspace_id,
            version=version,
            entities=[_deserialize_entity(entity) for entity in entity_rows],
            relations=[
                _deserialize_relation(
                    relation,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                )
                for relation, source_entity_id, target_entity_id in relation_rows
            ],
        )


def _replace_version_snapshot(tx, parameters: dict) -> None:
    tx.run(
        """
        MATCH (version:OntologyVersion)
        WHERE version.id = $version_id
        OPTIONAL MATCH (version)-[:HAS_ENTITY]->(entity:OntologyEntity)
        DETACH DELETE entity
        """,
        version_id=parameters["version"]["id"],
    )
    tx.run(
        """
        MATCH (version:OntologyVersion)
        WHERE version.id = $version_id
        DETACH DELETE version
        """,
        version_id=parameters["version"]["id"],
    )
    tx.run(
        """
        MERGE (workspace:Workspace {id: $workspace_id})
        MERGE (version:OntologyVersion {id: $version.id})
        SET version.workspace_id = $workspace_id,
            version.version_number = $version.version_number,
            version.source_build_id = $version.source_build_id,
            version.created_at = $version.created_at
        MERGE (workspace)-[:HAS_ONTOLOGY_VERSION]->(version)
        """,
        **parameters,
    )
    tx.run(
        """
        UNWIND $entities AS entity
        MATCH (version:OntologyVersion)
        WHERE version.id = $version_id
        CREATE (node:OntologyEntity {
            id: entity.id,
            version_id: entity.version_id,
            workspace_id: entity.workspace_id,
            resolution_key: entity.resolution_key,
            name: entity.name,
            entity_type: entity.entity_type,
            aliases: entity.aliases,
            source_build_id: entity.source_build_id,
            source_document_id: entity.source_document_id,
            created_at: entity.created_at
        })
        CREATE (version)-[:HAS_ENTITY]->(node)
        """,
        version_id=parameters["version"]["id"],
        entities=parameters["entities"],
    )
    tx.run(
        """
        UNWIND $relations AS relation
        MATCH (source:OntologyEntity)
        WHERE source.id = relation.source_entity_id AND source.version_id = relation.version_id
        MATCH (target:OntologyEntity)
        WHERE target.id = relation.target_entity_id AND target.version_id = relation.version_id
        MERGE (source)-[edge:ONTOLOGY_RELATION {id: relation.id}]->(target)
        SET edge.version_id = relation.version_id,
            edge.workspace_id = relation.workspace_id,
            edge.relation_type = relation.relation_type,
            edge.confidence = relation.confidence,
            edge.source_build_id = relation.source_build_id,
            edge.source_document_id = relation.source_document_id,
            edge.evidence_text = relation.evidence_text,
            edge.provenance = relation.provenance,
            edge.created_at = relation.created_at
        """,
        relations=parameters["relations"],
    )


def _serialize_version(version: OntologyVersionResponse) -> dict:
    return {
        "id": version.id,
        "workspace_id": version.workspace_id,
        "version_number": version.version_number,
        "source_build_id": version.source_build_id,
        "created_at": _serialize_datetime(version.created_at),
    }


def _serialize_entity(entity: OntologyEntityResponse) -> dict:
    return {
        "id": entity.id,
        "version_id": entity.version_id,
        "workspace_id": entity.workspace_id,
        "resolution_key": entity.resolution_key,
        "name": entity.name,
        "entity_type": entity.entity_type,
        "aliases": entity.aliases,
        "source_build_id": entity.source_build_id,
        "source_document_id": entity.source_document_id,
        "created_at": _serialize_datetime(entity.created_at),
    }


def _serialize_relation(relation: OntologyRelationResponse) -> dict:
    return {
        "id": relation.id,
        "version_id": relation.version_id,
        "workspace_id": relation.workspace_id,
        "source_entity_id": relation.source_entity_id,
        "target_entity_id": relation.target_entity_id,
        "relation_type": relation.relation_type,
        "confidence": relation.confidence,
        "source_build_id": relation.source_build_id,
        "source_document_id": relation.source_document_id,
        "evidence_text": relation.evidence_text,
        "provenance": json.dumps(relation.provenance, sort_keys=True),
        "created_at": _serialize_datetime(relation.created_at),
    }


def _deserialize_version(node) -> OntologyVersionResponse:
    data = dict(node)
    return OntologyVersionResponse(
        id=data["id"],
        workspace_id=data["workspace_id"],
        version_number=int(data["version_number"]),
        source_build_id=data["source_build_id"],
        created_at=_deserialize_datetime(data["created_at"]),
    )


def _deserialize_entity(node) -> OntologyEntityResponse:
    data = dict(node)
    return OntologyEntityResponse(
        id=data["id"],
        version_id=data["version_id"],
        workspace_id=data["workspace_id"],
        resolution_key=data["resolution_key"],
        name=data["name"],
        entity_type=data["entity_type"],
        aliases=list(data.get("aliases", [])),
        source_build_id=data["source_build_id"],
        source_document_id=data["source_document_id"],
        created_at=_deserialize_datetime(data["created_at"]),
    )


def _deserialize_relation(node, *, source_entity_id: str, target_entity_id: str) -> OntologyRelationResponse:
    data = dict(node)
    return OntologyRelationResponse(
        id=data["id"],
        version_id=data["version_id"],
        workspace_id=data["workspace_id"],
        source_entity_id=source_entity_id,
        target_entity_id=target_entity_id,
        relation_type=data["relation_type"],
        confidence=float(data["confidence"]),
        source_build_id=data["source_build_id"],
        source_document_id=data["source_document_id"],
        evidence_text=data["evidence_text"],
        provenance=_deserialize_json_map(data.get("provenance")),
        created_at=_deserialize_datetime(data["created_at"]),
    )


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _deserialize_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _deserialize_json_map(value: str | dict | None) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return json.loads(value)
