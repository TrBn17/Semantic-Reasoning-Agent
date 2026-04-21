import { apiFetch } from "@/shared/api/client";
import type {
  AgentProfileCreateRequest,
  AgentProfileResponse,
  AgentProfileUpdateRequest,
} from "@/shared/api/types";

export function listAgentProfiles(workspaceId?: string | null): Promise<AgentProfileResponse[]> {
  return apiFetch<AgentProfileResponse[]>("/agents/profiles", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}

export function createAgentProfile(
  payload: AgentProfileCreateRequest,
): Promise<AgentProfileResponse> {
  return apiFetch<AgentProfileResponse>("/agents/profiles", {
    method: "POST",
    body: payload,
  });
}

export function updateAgentProfile(
  id: string,
  payload: AgentProfileUpdateRequest,
): Promise<AgentProfileResponse> {
  return apiFetch<AgentProfileResponse>(`/agents/profiles/${id}`, {
    method: "PATCH",
    body: payload,
  });
}

export function setDefaultAgentProfile(id: string): Promise<AgentProfileResponse> {
  return apiFetch<AgentProfileResponse>(`/agents/profiles/${id}/set-default`, {
    method: "POST",
  });
}
