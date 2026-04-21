import type { VariantProps } from "class-variance-authority";
import type { badgeVariants } from "@/components/ui/badge";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

/** Provider/model catalog readiness — shared by agents UI. */
export function readinessBadgeVariant(ready: boolean): Extract<BadgeVariant, "success" | "warning"> {
  return ready ? "success" : "warning";
}
