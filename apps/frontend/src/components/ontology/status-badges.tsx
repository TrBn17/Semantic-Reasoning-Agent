import { Badge } from "@/components/ui/badge";
import type {
  OntologyBuildStatus,
  OntologyReviewStatus,
  OntologyStepStatus,
} from "@/shared/api/types";

const BUILD: Record<
  OntologyBuildStatus,
  "default" | "secondary" | "destructive" | "success" | "info" | "warning"
> = {
  pending: "secondary",
  running: "info",
  completed: "warning",
  failed: "destructive",
  published: "success",
};

const REVIEW: Record<
  OntologyReviewStatus,
  "default" | "secondary" | "destructive" | "success" | "info" | "warning"
> = {
  pending_review: "warning",
  approved: "success",
  rejected: "destructive",
};

const STEP: Record<
  OntologyStepStatus,
  "default" | "secondary" | "destructive" | "success" | "info" | "warning"
> = {
  pending: "secondary",
  running: "info",
  completed: "success",
  failed: "destructive",
};

export function BuildStatusBadge({ status }: { status: OntologyBuildStatus }) {
  return (
    <Badge variant={BUILD[status]} className="capitalize">
      {status}
    </Badge>
  );
}

export function ReviewStatusBadge({
  status,
}: {
  status: OntologyReviewStatus;
}) {
  return (
    <Badge variant={REVIEW[status]} className="capitalize">
      {status.replace("_", " ")}
    </Badge>
  );
}

export function StepStatusBadge({ status }: { status: OntologyStepStatus }) {
  return (
    <Badge variant={STEP[status]} className="capitalize">
      {status}
    </Badge>
  );
}
