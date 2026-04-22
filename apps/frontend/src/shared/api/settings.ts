import { apiFetch } from "@/shared/api/client";
import type {
  SettingsModelOption,
  SettingsResponse,
  SettingsUpdateRequest,
} from "@/shared/api/types";

export function getSettings(workspaceId?: string | null): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>("/settings", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}

export function updateSettings(payload: SettingsUpdateRequest): Promise<SettingsResponse> {
  return apiFetch<SettingsResponse>("/settings", {
    method: "PUT",
    body: payload,
  });
}

export function listSettingsModels(
  workspaceId?: string | null,
): Promise<SettingsModelOption[]> {
  return apiFetch<SettingsModelOption[]>("/settings/models", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}
