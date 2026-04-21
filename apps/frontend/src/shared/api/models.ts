import { apiFetch } from "@/shared/api/client";
import type { ModelOption } from "@/shared/api/types";

export function listModels(workspaceId?: string | null): Promise<ModelOption[]> {
  return apiFetch<ModelOption[]>("/models", {
    method: "GET",
    searchParams: { workspace_id: workspaceId ?? undefined },
  });
}
