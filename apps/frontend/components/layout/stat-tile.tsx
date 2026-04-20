import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type StatTileProps = {
  label: ReactNode;
  value: ReactNode;
  className?: string;
  size?: "sm" | "md";
};

/**
 * KPI / summary tile (unifies SummaryStat / SummaryTile / SummaryPill patterns).
 */
export function StatTile({
  label,
  value,
  className,
  size = "md",
}: StatTileProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border/60 bg-muted/40 p-4",
        size === "sm" && "p-3",
        className,
      )}
    >
      <div className="text-overline text-muted-foreground">{label}</div>
      <div
        className={cn(
          "mt-1 font-semibold tabular-nums text-foreground",
          size === "md" ? "text-2xl" : "text-lg",
        )}
      >
        {value}
      </div>
    </div>
  );
}
