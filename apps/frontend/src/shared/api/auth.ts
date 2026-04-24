import { apiFetch } from "@/shared/api/client";
import type {
  AuthMeResponse,
  WorkspaceCreateRequest,
  WorkspaceSummary,
  WorkspaceUpdateRequest,
} from "@/shared/api/types";

export function fetchMe(): Promise<AuthMeResponse> {
  return apiFetch<AuthMeResponse>("/auth/me", { method: "GET" });
}

export function fetchWorkspaces(): Promise<WorkspaceSummary[]> {
  return apiFetch<WorkspaceSummary[]>("/auth/workspaces", { method: "GET" });
}

export function createWorkspace(payload: WorkspaceCreateRequest): Promise<WorkspaceSummary> {
  return apiFetch<WorkspaceSummary>("/auth/workspaces", {
    method: "POST",
    body: payload,
  });
}

export function updateWorkspace(
  workspaceId: string,
  payload: WorkspaceUpdateRequest,
): Promise<WorkspaceSummary> {
  return apiFetch<WorkspaceSummary>(`/auth/workspaces/${workspaceId}`, {
    method: "PATCH",
    body: payload,
  });
}

export function deleteWorkspace(workspaceId: string): Promise<void> {
  return apiFetch<void>(`/auth/workspaces/${workspaceId}`, { method: "DELETE" });
}
