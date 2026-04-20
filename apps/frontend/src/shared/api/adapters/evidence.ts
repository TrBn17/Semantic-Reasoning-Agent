import type {
  Citation,
  OntologyCandidateEntityResponse,
  OntologyCandidateRelationResponse,
  OntologyEntityResponse,
  OntologyRelationResponse,
  RetrievalResult,
} from "@/lib/api/types";
import type {
  EvidenceItemViewModel,
  EvidenceSourceType,
} from "@/src/entities/evidence/types";

export function retrievalResultToEvidence(
  r: RetrievalResult,
): EvidenceItemViewModel {
  return {
    id: `retrieval:${r.chunk_id}`,
    sourceType: "retrieval_citation" satisfies EvidenceSourceType,
    title: r.document_title || r.chunk_id,
    summary: r.excerpt,
    contentSnippet: r.citation.excerpt,
    score: r.score,
    citationLabel: r.citation.location_label,
    locator: r.citation.location_label,
    documentId: r.document_id,
    uri: r.citation.source_url || undefined,
    provenanceSummary: buildCitationProvenance(r.citation),
  };
}

export function citationToEvidence(c: Citation): EvidenceItemViewModel {
  return {
    id: `citation:${c.chunk_id}`,
    sourceType: "document_chunk" satisfies EvidenceSourceType,
    title: c.document_title || c.chunk_id,
    contentSnippet: c.excerpt,
    citationLabel: c.location_label,
    locator: c.location_label,
    documentId: c.document_id,
    uri: c.source_url || undefined,
    provenanceSummary: buildCitationProvenance(c),
  };
}

export function candidateEntityToEvidence(
  e: OntologyCandidateEntityResponse,
): EvidenceItemViewModel {
  return {
    id: `entity:${e.id}`,
    sourceType: "ontology_candidate_entity" satisfies EvidenceSourceType,
    title: e.name || e.canonical_name,
    summary: `${e.entity_type} · ${e.status}`,
    contentSnippet: e.evidence_text,
    score: e.confidence,
    trustScore: e.confidence,
    documentId: e.document_id,
    buildId: e.build_id,
    entityId: e.id,
    provenanceSummary: summarizeProvenance(e.provenance),
  };
}

export function candidateRelationToEvidence(
  r: OntologyCandidateRelationResponse,
): EvidenceItemViewModel {
  return {
    id: `relation:${r.id}`,
    sourceType: "ontology_candidate_relation" satisfies EvidenceSourceType,
    title: `${r.source_name} — ${r.relation_type} → ${r.target_name}`,
    summary: `${r.relation_type} · ${r.status}`,
    contentSnippet: r.evidence_text,
    score: r.confidence,
    trustScore: r.confidence,
    documentId: r.document_id,
    buildId: r.build_id,
    relationId: r.id,
    provenanceSummary: summarizeProvenance(r.provenance),
  };
}

function buildCitationProvenance(c: Citation): string {
  const parts: string[] = [];
  if (c.heading_path) parts.push(c.heading_path);
  if (c.page_number != null) parts.push(`p.${c.page_number}`);
  if (c.sheet_name) parts.push(c.sheet_name);
  if (c.row_start != null) {
    parts.push(
      c.row_end != null && c.row_end !== c.row_start
        ? `rows ${c.row_start}-${c.row_end}`
        : `row ${c.row_start}`,
    );
  }
  return parts.join(" · ");
}

function summarizeProvenance(p: Record<string, unknown>): string | undefined {
  if (!p || Object.keys(p).length === 0) return undefined;
  const keys = Object.keys(p).slice(0, 3).join(", ");
  return keys;
}

/** Published graph entities (GET /knowledge-graph). */
export function publishedEntityToEvidence(e: OntologyEntityResponse): EvidenceItemViewModel {
  return {
    id: `graph-entity:${e.id}`,
    sourceType: "ontology_graph_entity" satisfies EvidenceSourceType,
    title: e.name,
    summary: e.entity_type,
    contentSnippet: e.aliases.join(", ") || undefined,
    documentId: e.source_document_id,
    entityId: e.id,
    provenanceSummary: `v:${e.version_id.slice(0, 8)}…`,
  };
}

/** Published graph relations (GET /knowledge-graph). */
export function publishedRelationToEvidence(r: OntologyRelationResponse): EvidenceItemViewModel {
  return {
    id: `graph-relation:${r.id}`,
    sourceType: "ontology_graph_relation" satisfies EvidenceSourceType,
    title: `${r.relation_type}`,
    summary: `${r.source_entity_id} → ${r.target_entity_id}`,
    contentSnippet: r.evidence_text,
    score: r.confidence,
    trustScore: r.confidence,
    documentId: r.source_document_id,
    relationId: r.id,
    provenanceSummary: summarizeProvenance(r.provenance),
  };
}
