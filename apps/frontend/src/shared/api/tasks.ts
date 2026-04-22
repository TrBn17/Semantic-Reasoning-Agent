import { apiFetch } from "@/shared/api/client";
import type {
  TaskResolveRequest,
  TaskResolveResponse,
  TaskRunRecord,
  ToolCallRecord,
} from "@/shared/api/types";

export function resolveTask(
  payload: TaskResolveRequest,
): Promise<TaskResolveResponse> {
  return apiFetch<TaskResolveResponse>("/tasks/resolve", {
    method: "POST",
    body: payload,
  });
}

export function listTasks(): Promise<TaskRunRecord[]> {
  return apiFetch<TaskRunRecord[]>("/tasks", { method: "GET" });
}

export function getTask(taskId: string): Promise<TaskRunRecord> {
  return apiFetch<TaskRunRecord>(`/tasks/${taskId}`, { method: "GET" });
}

export function listTaskToolCalls(taskId: string): Promise<ToolCallRecord[]> {
  return apiFetch<ToolCallRecord[]>(`/tasks/${taskId}/tool-calls`, {
    method: "GET",
  });
}
