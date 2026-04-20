import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type EmptyPanelProps = {
  title?: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  className?: string;
  /** Default: dashed border list empty state */
  variant?: "dashed" | "muted";
};

const variantClass: Record<NonNullable<EmptyPanelProps["variant"]>, string> = {
  dashed:
    "rounded-2xl border border-dashed border-border/70 bg-muted/20 p-8 text-center text-sm text-muted-foreground",
  muted: "rounded-xl border border-border/60 bg-muted/40 p-6 text-center text-sm text-muted-foreground",
};

/**
 * Unified empty state (replaces 10+ copy-paste dashed boxes).
 */
export function EmptyPanel({
  title,
  description,
  children,
  className,
  variant = "dashed",
}: EmptyPanelProps) {
  return (
    <div className={cn(variantClass[variant], className)}>
      {title != null ? (
        <p className="font-medium text-foreground">{title}</p>
      ) : null}
      {description != null ? (
        <p
          className={cn(
            title != null ? "mt-1 text-muted-foreground" : "text-muted-foreground",
          )}
        >
          {description}
        </p>
      ) : null}
      {children}
    </div>
  );
}
