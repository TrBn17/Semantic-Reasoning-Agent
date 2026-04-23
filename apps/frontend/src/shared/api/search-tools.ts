import { apiFetch } from "@/shared/api/client";
import type {
  SearchToolConfigCreateRequest,
  SearchToolConfigResponse,
  SearchToolConfigUpdateRequest,
  SearchToolRunRequest,
  SearchToolRunResponse,
  SearchToolType,
} from "@/shared/api/types";

export function listSearchTools(params?: {
  workspaceId?: string;
  toolType?: SearchToolType;
}): Promise<SearchToolConfigResponse[]> {
  return apiFetch<SearchToolConfigResponse[]>("/search-tools", {
    method: "GET",
    searchParams: {
      workspace_id: params?.workspaceId,
      tool_type: params?.toolType,
    },
  });
}

export function createSearchTool(
  payload: SearchToolConfigCreateRequest,
): Promise<SearchToolConfigResponse> {
  return apiFetch<SearchToolConfigResponse>("/search-tools", {
    method: "POST",
    body: payload,
  });
}

export function updateSearchTool(
  id: string,
  payload: SearchToolConfigUpdateRequest,
  workspaceId?: string,
): Promise<SearchToolConfigResponse> {
  return apiFetch<SearchToolConfigResponse>(`/search-tools/${id}`, {
    method: "PATCH",
    body: payload,
    searchParams: { workspace_id: workspaceId },
  });
}

export function deleteSearchTool(id: string, workspaceId?: string): Promise<void> {
  return apiFetch<void>(`/search-tools/${id}`, {
    method: "DELETE",
    searchParams: { workspace_id: workspaceId },
  });
}

export function runSearchTool(
  id: string,
  payload: SearchToolRunRequest,
  workspaceId?: string,
): Promise<SearchToolRunResponse> {
  return apiFetch<SearchToolRunResponse>(`/search-tools/${id}/run`, {
    method: "POST",
    body: payload,
    searchParams: { workspace_id: workspaceId },
  });
}
