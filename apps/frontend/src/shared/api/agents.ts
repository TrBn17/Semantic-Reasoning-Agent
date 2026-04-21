import { apiFetch } from "@/shared/api/client";
import type {
  AgentSettingsResponse,
  AgentSettingsUpdateRequest,
} from "@/shared/api/types";

export function getAgentSettings(workspaceId?: string | null): Promise<AgentSettingsResponse> {
  return apiFetch<AgentSettingsResponse>("/agents/settings", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}

export function updateAgentSettings(
  payload: AgentSettingsUpdateRequest,
): Promise<AgentSettingsResponse> {
  return apiFetch<AgentSettingsResponse>("/agents/settings", {
    method: "PUT",
    body: payload,
  });
}
