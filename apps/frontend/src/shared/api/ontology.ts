import { apiFetch } from "@/shared/api/client";
import type {
  OntologyBuildCreateRequest,
  OntologyBuildResponse,
  OntologyCandidateEntityResponse,
  OntologyCandidateEntityUpdateRequest,
  OntologyCandidateRelationResponse,
  OntologyCandidateRelationUpdateRequest,
  OntologyGraphResponse,
  OntologyPublishResponse,
  OntologyReviewRequest,
  OntologyReviewStatus,
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

export function listBuildEntities(
  buildId: string,
  reviewStatus?: OntologyReviewStatus,
): Promise<OntologyCandidateEntityResponse[]> {
  return apiFetch<OntologyCandidateEntityResponse[]>(
    `/ontology/builds/${buildId}/entities`,
    {
      method: "GET",
      searchParams: reviewStatus ? { review_status: reviewStatus } : undefined,
    },
  );
}

export function listBuildRelations(
  buildId: string,
  reviewStatus?: OntologyReviewStatus,
): Promise<OntologyCandidateRelationResponse[]> {
  return apiFetch<OntologyCandidateRelationResponse[]>(
    `/ontology/builds/${buildId}/relations`,
    {
      method: "GET",
      searchParams: reviewStatus ? { review_status: reviewStatus } : undefined,
    },
  );
}

export function reviewEntity(
  entityId: string,
  body: OntologyReviewRequest,
): Promise<OntologyCandidateEntityResponse> {
  return apiFetch<OntologyCandidateEntityResponse>(`/ontology/entities/${entityId}/review`, {
    method: "POST",
    body,
  });
}

export function updateEntity(
  entityId: string,
  body: OntologyCandidateEntityUpdateRequest,
): Promise<OntologyCandidateEntityResponse> {
  return apiFetch<OntologyCandidateEntityResponse>(`/ontology/entities/${entityId}`, {
    method: "PATCH",
    body,
  });
}

export function updateRelation(
  relationId: string,
  body: OntologyCandidateRelationUpdateRequest,
): Promise<OntologyCandidateRelationResponse> {
  return apiFetch<OntologyCandidateRelationResponse>(`/ontology/relations/${relationId}`, {
    method: "PATCH",
    body,
  });
}

export function reviewRelation(
  relationId: string,
  body: OntologyReviewRequest,
): Promise<OntologyCandidateRelationResponse> {
  return apiFetch<OntologyCandidateRelationResponse>(
    `/ontology/relations/${relationId}/review`,
    {
      method: "POST",
      body,
    },
  );
}

export function publishBuild(buildId: string): Promise<OntologyPublishResponse> {
  return apiFetch<OntologyPublishResponse>(`/ontology/builds/${buildId}/publish`, {
    method: "POST",
  });
}

export function getGraph(workspaceId?: string): Promise<OntologyGraphResponse> {
  return apiFetch<OntologyGraphResponse>("/ontology/graph", {
    method: "GET",
    searchParams: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
}
