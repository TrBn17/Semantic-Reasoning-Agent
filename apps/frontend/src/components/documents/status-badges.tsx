import { Badge } from "@/components/ui/badge";
import type { DocumentStatus, JobStatus } from "@/shared/api/types";

const DOCUMENT_VARIANT: Record<
  DocumentStatus,
  "default" | "secondary" | "destructive" | "success" | "info" | "warning"
> = {
  uploaded: "info",
  parsed: "warning",
  indexed: "success",
  failed: "destructive",
};

const JOB_VARIANT: Record<
  JobStatus,
  "default" | "secondary" | "destructive" | "success" | "info" | "warning"
> = {
  pending: "secondary",
  running: "info",
  completed: "success",
  failed: "destructive",
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <Badge variant={DOCUMENT_VARIANT[status]} className="capitalize">
      {status}
    </Badge>
  );
}

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <Badge variant={JOB_VARIANT[status]} className="capitalize">
      {status}
    </Badge>
  );
}
