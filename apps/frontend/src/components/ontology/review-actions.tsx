"use client";

import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ReviewActions({
  status,
  onApprove,
  onReject,
  pending,
}: {
  status: string;
  onApprove: () => void;
  onReject: () => void;
  pending?: boolean;
}) {
  if (status !== "pending_review") return null;
  return (
    <div className="flex gap-2">
      <Button
        size="sm"
        variant="outline"
        onClick={onApprove}
        disabled={pending}
      >
        <Check className="h-4 w-4" />
        Approve
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={onReject}
        disabled={pending}
        className="text-destructive"
      >
        <X className="h-4 w-4" />
        Reject
      </Button>
    </div>
  );
}
