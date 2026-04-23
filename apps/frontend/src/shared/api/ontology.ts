import { apiFetch } from "@/shared/api/client";
import type {
  OntologyBuildCreateRequest,
  OntologyBuildResponse,
  OntologyGraphResponse,
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
