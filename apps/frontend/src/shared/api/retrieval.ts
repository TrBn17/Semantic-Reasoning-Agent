import { apiFetch } from "@/shared/api/client";
import type {
  RetrievalReindexRequest,
  RetrievalReindexResponse,
  RetrievalSearchRequest,
  RetrievalSearchResponse,
} from "@/shared/api/types";

export function searchRetrieval(
  payload: RetrievalSearchRequest,
): Promise<RetrievalSearchResponse> {
  return apiFetch<RetrievalSearchResponse>("/retrieval/search", {
    method: "POST",
    body: payload,
  });
}

export function reindexDocuments(
  payload: RetrievalReindexRequest,
): Promise<RetrievalReindexResponse> {
  return apiFetch<RetrievalReindexResponse>("/retrieval/reindex", {
    method: "POST",
    body: payload,
  });
}
