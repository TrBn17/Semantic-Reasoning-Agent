import { apiFetch } from "@/shared/api/client";
import type { AuthMeResponse } from "@/shared/api/types";

export function fetchMe(): Promise<AuthMeResponse> {
  return apiFetch<AuthMeResponse>("/auth/me", { method: "GET" });
}
