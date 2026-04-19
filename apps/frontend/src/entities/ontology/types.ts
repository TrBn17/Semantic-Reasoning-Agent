export type OntologyReviewItemViewModel = {
  id: string;
  buildId: string;
  itemType: "entity" | "relation";
  label: string;
  candidateType?: string;
  confidence?: number;
  status: "pending_review" | "approved" | "rejected";
  provenanceSummary?: string;
};

export type GraphNodeViewModel = {
  id: string;
  name: string;
  entityType: string;
  aliases: string[];
  sourceDocumentId: string;
};

export type GraphEdgeViewModel = {
  id: string;
  sourceId: string;
  targetId: string;
  relationType: string;
  confidence: number;
  evidenceText?: string;
};
