import { apiFetch } from "@/shared/api/client";
import type {
  TaskResolutionRequest,
  TaskResolutionResponse,
  WorkflowRunRecord,
  WorkflowSpec,
} from "@/shared/api/types";

export function listWorkflows(): Promise<WorkflowSpec[]> {
  return apiFetch<WorkflowSpec[]>("/workflows", { method: "GET" });
}

export function listWorkflowRuns(): Promise<WorkflowRunRecord[]> {
  return apiFetch<WorkflowRunRecord[]>("/workflows/runs", { method: "GET" });
}

export function runWorkflow(
  workflowId: string,
  payload: TaskResolutionRequest,
): Promise<TaskResolutionResponse> {
  return apiFetch<TaskResolutionResponse>(`/workflows/${workflowId}/run`, {
    method: "POST",
    body: payload,
  });
}
