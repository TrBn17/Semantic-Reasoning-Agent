import { apiFetch } from "@/shared/api/client";
import type {
  OntologyBuildCreateRequest,
  OntologyBuildResponse,
  OntologyDraftPublishRequest,
  OntologyGraphDraftResponse,
  OntologyGraphProjectionCreateRequest,
  OntologyGraphProjectionResponse,
  OntologyGraphResponse,
  OntologyPublishResponse,
} from "@/shared/api/types";

export {
  deleteKnowledgeGraph,
  extractAndPublish,
  getKnowledgeGraph,
  ingestFilesAndPublish,
  patchKnowledgeGraphRelation,
} from "@/shared/api/knowledge-graph";

export function createBuild(
  body: OntologyBuildCreateRequest,
): Promise<OntologyBuildResponse> {
  return apiFetch<OntologyBuildResponse>("/ontology/builds", {
    method: "POST",
    body,
  });
}

export function listBuilds(workspaceId?: string): Promise<OntologyBuildResponse[]> {
  return apiFetch<OntologyBuildResponse[]>("/ontology/builds", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

export function getBuild(buildId: string): Promise<OntologyBuildResponse> {
  return apiFetch<OntologyBuildResponse>(`/ontology/builds/${buildId}`, {
    method: "GET",
  });
}

export function deleteBuild(buildId: string): Promise<void> {
  return apiFetch<void>(`/ontology/builds/${buildId}`, {
    method: "DELETE",
  });
}

export function getGraph(workspaceId?: string): Promise<OntologyGraphResponse> {
  return apiFetch<OntologyGraphResponse>("/ontology/graph", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

/** Latest published ontology merged with workspace draft edits (relations/nodes removed here). */
export function getGraphDraft(workspaceId?: string): Promise<OntologyGraphDraftResponse> {
  return apiFetch<OntologyGraphDraftResponse>("/ontology/graph/draft", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

/** Removes the relation from the merged view via draft patch; publish separately to persist. */
export function deleteGraphDraftRelation(
  relationId: string,
  workspaceId?: string,
): Promise<OntologyGraphDraftResponse> {
  return apiFetch<OntologyGraphDraftResponse>(
    `/ontology/graph/draft/relations/${encodeURIComponent(relationId)}`,
    {
      method: "DELETE",
      searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
    },
  );
}

/** Removes the entity and incident draft relations via draft patches; publish separately to persist. */
export function deleteGraphDraftNode(
  nodeId: string,
  workspaceId?: string,
): Promise<OntologyGraphDraftResponse> {
  return apiFetch<OntologyGraphDraftResponse>(
    `/ontology/graph/draft/nodes/${encodeURIComponent(nodeId)}`,
    {
      method: "DELETE",
      searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
    },
  );
}

/** Clear all draft edits for this workspace draft row. */
export function resetGraphDraft(workspaceId?: string): Promise<OntologyGraphDraftResponse> {
  return apiFetch<OntologyGraphDraftResponse>("/ontology/graph/draft/reset", {
    method: "POST",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

export function publishGraphDraft(body: OntologyDraftPublishRequest): Promise<OntologyPublishResponse> {
  return apiFetch<OntologyPublishResponse>("/ontology/graph/draft/publish", {
    method: "POST",
    body,
  });
}

export function listGraphProjections(
  workspaceId?: string | null,
): Promise<OntologyGraphProjectionResponse[]> {
  return apiFetch<OntologyGraphProjectionResponse[]>("/ontology/graph-projections", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}

export function createGraphProjection(
  body: OntologyGraphProjectionCreateRequest,
): Promise<OntologyGraphProjectionResponse> {
  return apiFetch<OntologyGraphProjectionResponse>("/ontology/graph-projections", {
    method: "POST",
    body,
  });
}

export function deleteGraphProjection(projectionId: string): Promise<void> {
  return apiFetch<void>(`/ontology/graph-projections/${encodeURIComponent(projectionId)}`, {
    method: "DELETE",
  });
}
