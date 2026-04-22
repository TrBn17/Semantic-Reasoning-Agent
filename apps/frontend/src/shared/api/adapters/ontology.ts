import type {
  OntologyCandidateEntityResponse,
  OntologyCandidateRelationResponse,
  OntologyEntityResponse,
  OntologyRelationResponse,
} from "@/shared/api/types";
import type {
  GraphEdgeViewModel,
  GraphNodeViewModel,
  OntologyReviewItemViewModel,
} from "@/entities/ontology/types";

export function candidateEntityToReviewItem(
  e: OntologyCandidateEntityResponse,
): OntologyReviewItemViewModel {
  return {
    id: e.id,
    buildId: e.build_id,
    itemType: "entity",
    label: e.name || e.canonical_name,
    candidateType: e.entity_type,
    confidence: e.confidence,
    status: e.status,
    provenanceSummary: e.evidence_text,
  };
}

export function candidateRelationToReviewItem(
  r: OntologyCandidateRelationResponse,
): OntologyReviewItemViewModel {
  return {
    id: r.id,
    buildId: r.build_id,
    itemType: "relation",
    label: `${r.source_name} -> ${r.target_name}`,
    candidateType: r.relation_type,
    confidence: r.confidence,
    status: r.status,
    provenanceSummary: r.evidence_text,
  };
}

export function entityToNode(e: OntologyEntityResponse): GraphNodeViewModel {
  return {
    id: e.id,
    name: e.name,
    entityType: e.entity_type,
    resolutionKey: e.resolution_key,
    aliases: e.aliases,
    sourceDocumentId: e.source_document_id,
    sourceBuildId: e.source_build_id,
  };
}

export function relationToEdge(r: OntologyRelationResponse): GraphEdgeViewModel {
  return {
    id: r.id,
    sourceId: r.source_entity_id,
    targetId: r.target_entity_id,
    relationType: r.relation_type,
    confidence: r.confidence,
    evidenceText: r.evidence_text,
    sourceBuildId: r.source_build_id,
    sourceDocumentId: r.source_document_id,
  };
}
