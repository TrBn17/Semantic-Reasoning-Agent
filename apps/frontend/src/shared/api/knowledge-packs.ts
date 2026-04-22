import { apiFetch } from "@/shared/api/client";
import type {
  KnowledgePackCreateRequest,
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
