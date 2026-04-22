import { apiFetch } from "@/shared/api/client";
import type {
  AgentCapabilityCatalogResponse,
  AgentCapabilityToolSchema,
} from "@/shared/api/types";

export function getCapabilityCatalog(): Promise<AgentCapabilityCatalogResponse> {
  return apiFetch<AgentCapabilityCatalogResponse>("/agent-capabilities/catalog", {
    method: "GET",
  });
}

export function listCapabilityTools(): Promise<AgentCapabilityToolSchema[]> {
  return apiFetch<AgentCapabilityToolSchema[]>("/agent-capabilities/tools", {
    method: "GET",
  });
}
