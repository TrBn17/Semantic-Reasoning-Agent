import { apiFetch } from "@/shared/api/client";
import type { AuthMeResponse, WorkspaceSummary } from "@/shared/api/types";

export function fetchMe(): Promise<AuthMeResponse> {
  return apiFetch<AuthMeResponse>("/auth/me", { method: "GET" });
}

export function fetchWorkspaces(): Promise<WorkspaceSummary[]> {
  return apiFetch<WorkspaceSummary[]>("/auth/workspaces", { method: "GET" });
}
