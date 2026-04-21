import { apiFetch } from "@/shared/api/client";
import type { StandardToolInput, StandardToolOutput, ToolSpec } from "@/shared/api/types";

export function listTools(params?: { family?: string; maxRisk?: string }): Promise<ToolSpec[]> {
  return apiFetch<ToolSpec[]>("/tools", {
    method: "GET",
    searchParams: {
      family: params?.family,
      max_risk: params?.maxRisk,
    },
  });
}

export function invokeTool(toolName: string, payload: StandardToolInput): Promise<StandardToolOutput> {
  return apiFetch<StandardToolOutput>(`/tools/${toolName}/invoke`, {
    method: "POST",
    body: payload,
  });
}