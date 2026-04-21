import { apiFetch } from "@/shared/api/client";
import type {
  KnowledgeGraphExtractRequest,
  KnowledgeGraphIngestResponse,
  KnowledgeGraphRelationPatch,
  OntologyGraphResponse,
  OntologyPublishResponse,
  OntologyRelationResponse,
} from "@/shared/api/types";

/** GET /knowledge-graph */
export function getKnowledgeGraph(workspaceId?: string): Promise<OntologyGraphResponse> {
  return apiFetch<OntologyGraphResponse>("/knowledge-graph", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

/** DELETE /knowledge-graph */
export function deleteKnowledgeGraph(workspaceId?: string): Promise<void> {
  return apiFetch<void>("/knowledge-graph", {
    method: "DELETE",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

/** POST /knowledge-graph/extract */
export function extractAndPublish(
  body: KnowledgeGraphExtractRequest,
): Promise<OntologyPublishResponse> {
  return apiFetch<OntologyPublishResponse>("/knowledge-graph/extract", {
    method: "POST",
    body,
  });
}

/** POST /knowledge-graph/ingest (multipart) */
export function ingestFilesAndPublish(
  files: File[],
  workspaceId?: string | null,
): Promise<KnowledgeGraphIngestResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  if (workspaceId) {
    form.append("workspace_id", workspaceId);
  }
  return apiFetch<KnowledgeGraphIngestResponse>("/knowledge-graph/ingest", {
    method: "POST",
    body: form,
  });
}

/** PATCH /knowledge-graph/relations/{relation_id} */
export function patchKnowledgeGraphRelation(
  relationId: string,
  body: KnowledgeGraphRelationPatch,
): Promise<OntologyRelationResponse> {
  return apiFetch<OntologyRelationResponse>(`/knowledge-graph/relations/${relationId}`, {
    method: "PATCH",
    body,
  });
}

/** @deprecated Use getKnowledgeGraph — kept for gradual import migration */
export const getGraph = getKnowledgeGraph;
