import { apiFetch } from "@/shared/api/client";
import type {
  KnowledgePackAddDocumentRequest,
  KnowledgePackCreateRequest,
  KnowledgePackDocumentSummaryResponse,
  KnowledgePackResponse,
  KnowledgePackUpdateRequest,
} from "@/shared/api/types";

export function listKnowledgePacks(
  workspaceId?: string | null,
): Promise<KnowledgePackResponse[]> {
  return apiFetch<KnowledgePackResponse[]>("/knowledge-packs", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}

export function createKnowledgePack(
  payload: KnowledgePackCreateRequest,
): Promise<KnowledgePackResponse> {
  return apiFetch<KnowledgePackResponse>("/knowledge-packs", {
    method: "POST",
    body: payload,
  });
}

export function updateKnowledgePack(
  id: string,
  payload: KnowledgePackUpdateRequest,
): Promise<KnowledgePackResponse> {
  return apiFetch<KnowledgePackResponse>(`/knowledge-packs/${id}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getKnowledgePack(id: string): Promise<KnowledgePackResponse> {
  return apiFetch<KnowledgePackResponse>(`/knowledge-packs/${id}`, {
    method: "GET",
  });
}

export function deleteKnowledgePack(id: string): Promise<void> {
  return apiFetch<void>(`/knowledge-packs/${id}`, {
    method: "DELETE",
  });
}

export function listKnowledgePackDocuments(
  id: string,
): Promise<KnowledgePackDocumentSummaryResponse[]> {
  return apiFetch<KnowledgePackDocumentSummaryResponse[]>(`/knowledge-packs/${id}/documents`, {
    method: "GET",
  });
}

export function addKnowledgePackDocument(
  id: string,
  payload: KnowledgePackAddDocumentRequest,
): Promise<KnowledgePackDocumentSummaryResponse[]> {
  return apiFetch<KnowledgePackDocumentSummaryResponse[]>(`/knowledge-packs/${id}/documents`, {
    method: "POST",
    body: payload,
  });
}

export function removeKnowledgePackDocument(
  id: string,
  documentId: string,
): Promise<KnowledgePackDocumentSummaryResponse[]> {
  return apiFetch<KnowledgePackDocumentSummaryResponse[]>(
    `/knowledge-packs/${id}/documents/${documentId}`,
    {
      method: "DELETE",
    },
  );
}
