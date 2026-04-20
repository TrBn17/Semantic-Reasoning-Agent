"""ORM → API schema mappers for ontology builds and published graph rows."""

from semantic_reasoning_agent.domain.ontology.pipeline_steps import ONTOLOGY_BUILD_STEP_NAMES
from semantic_reasoning_agent.persistence.models.ontology import (
    OntologyBuildStepORM,
    OntologyEntityORM,
    OntologyRelationORM,
    OntologyVersionORM,
)
from semantic_reasoning_agent.schemas.ontology import (
    OntologyBuildStepResponse,
    OntologyEntityResponse,
    OntologyRelationResponse,
    OntologyStepStatus,
    OntologyVersionResponse,
)


def build_step_records(build_id: str) -> list[OntologyBuildStepORM]:
    return [
        OntologyBuildStepORM(
            id=f"{build_id}:{name}",
            build_id=build_id,
            name=name,
            status=OntologyStepStatus.pending.value,
            detail=None,
            started_at=None,
            finished_at=None,
        )
        for name in ONTOLOGY_BUILD_STEP_NAMES
    ]


def step_sort_key(step: OntologyBuildStepORM) -> int:
    if step.name in ONTOLOGY_BUILD_STEP_NAMES:
        return ONTOLOGY_BUILD_STEP_NAMES.index(step.name)
    return len(ONTOLOGY_BUILD_STEP_NAMES)


def step_to_response(step: OntologyBuildStepORM) -> OntologyBuildStepResponse:
    return OntologyBuildStepResponse(
        id=step.id,
        name=step.name,
        status=step.status,
        detail=step.detail,
        started_at=step.started_at,
        finished_at=step.finished_at,
    )


def version_to_response(version: OntologyVersionORM) -> OntologyVersionResponse:
    return OntologyVersionResponse(
        id=version.id,
        workspace_id=version.workspace_id,
        version_number=version.version_number,
        source_build_id=version.source_build_id,
        created_at=version.created_at,
        entity_count=len(version.entities),
        relation_count=len(version.relations),
    )


def entity_to_response(entity: OntologyEntityORM) -> OntologyEntityResponse:
    return OntologyEntityResponse(
        id=entity.id,
        version_id=entity.version_id,
        workspace_id=entity.workspace_id,
        resolution_key=entity.resolution_key,
        name=entity.name,
        entity_type=entity.entity_type,
        aliases=entity.aliases or [],
        source_build_id=entity.source_build_id,
        source_document_id=entity.source_document_id,
        created_at=entity.created_at,
    )


def relation_to_response(relation: OntologyRelationORM) -> OntologyRelationResponse:
    return OntologyRelationResponse(
        id=relation.id,
        version_id=relation.version_id,
        workspace_id=relation.workspace_id,
        source_entity_id=relation.source_entity_id,
        target_entity_id=relation.target_entity_id,
        relation_type=relation.relation_type,
        confidence=relation.confidence,
        source_build_id=relation.source_build_id,
        source_document_id=relation.source_document_id,
        evidence_text=relation.evidence_text,
        provenance=relation.provenance or {},
        created_at=relation.created_at,
    )
