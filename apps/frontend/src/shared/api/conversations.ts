import { apiFetch } from "@/shared/api/client";
import type {
  ConversationAgentProfileRequest,
  ConversationCreateRequest,
  ConversationModelSelectionRequest,
  ConversationResponse,
} from "@/shared/api/types";

export function listConversations(): Promise<ConversationResponse[]> {
  return apiFetch<ConversationResponse[]>("/conversations", { method: "GET" });
}

export function getConversation(id: string): Promise<ConversationResponse> {
  return apiFetch<ConversationResponse>(`/conversations/${id}`, { method: "GET" });
}

export function createConversation(
  payload: ConversationCreateRequest,
): Promise<ConversationResponse> {
  return apiFetch<ConversationResponse>("/conversations", {
    method: "POST",
    body: payload,
  });
}

export function updateConversationModelSelection(
  id: string,
  payload: ConversationModelSelectionRequest,
): Promise<ConversationResponse> {
  return apiFetch<ConversationResponse>(`/conversations/${id}/model-selection`, {
    method: "PATCH",
    body: payload,
  });
}

export function updateConversationAgentProfile(
  id: string,
  payload: ConversationAgentProfileRequest,
): Promise<ConversationResponse> {
  return apiFetch<ConversationResponse>(`/conversations/${id}/agent-profile`, {
    method: "PATCH",
    body: payload,
  });
}
