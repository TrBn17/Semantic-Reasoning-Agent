export type TaskRunViewModel = {
  id: string;
  type: string;
  title: string;
  status:
    | "queued"
    | "running"
    | "completed"
    | "failed"
    | "needs_review";
  startedAt?: string;
  finishedAt?: string;
  workflowName?: string;
  summary?: string;
};
