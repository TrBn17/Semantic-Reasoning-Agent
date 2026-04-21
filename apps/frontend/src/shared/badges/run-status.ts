import type { VariantProps } from "class-variance-authority";
import type { badgeVariants } from "@/components/ui/badge";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/** Task runs, workflow runs, tool call rows — shared status→badge mapping. */
export function runStatusBadgeVariant(status: string): BadgeVariant {
  const s = status.toLowerCase();
  if (s === "completed" || s === "success") return "success";
  if (s === "failed" || s === "error") return "destructive";
  if (s === "running" || s === "pending" || s === "queued") return "info";
  return "warning";
}
