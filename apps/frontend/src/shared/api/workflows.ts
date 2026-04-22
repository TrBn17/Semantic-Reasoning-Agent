import { apiFetch } from "@/shared/api/client";
import type {
  TaskResolveRequest,
  TaskResolveResponse,
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
  payload: TaskResolveRequest,
): Promise<TaskResolveResponse> {
  return apiFetch<TaskResolveResponse>(`/workflows/${workflowId}/run`, {
    method: "POST",
    body: payload,
  });
}
