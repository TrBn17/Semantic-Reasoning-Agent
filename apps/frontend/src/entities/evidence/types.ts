export type EvidenceSourceType =
  | "document_chunk"
  | "ontology_candidate_entity"
  | "ontology_candidate_relation"
  | "retrieval_citation";

export type EvidenceItemViewModel = {
  id: string;
  sourceType: EvidenceSourceType;
  title: string;
  summary?: string;
  contentSnippet?: string;
  score?: number;
  trustScore?: number;
  freshnessTs?: string;
  citationLabel?: string;
  locator?: string;
  documentId?: string;
  buildId?: string;
  entityId?: string;
  relationId?: string;
  uri?: string;
  provenanceSummary?: string;
  relatedEntityIds?: string[];
  relatedRelationIds?: string[];
  promoted?: boolean;
};
