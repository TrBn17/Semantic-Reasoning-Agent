import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const maxWidthClass = {
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
  full: "max-w-none",
} as const;

export type PageShellMaxWidth = keyof typeof maxWidthClass;

type PageShellProps = {
  children: ReactNode;
  className?: string;
  /** Default: centered column with horizontal padding */
  maxWidth?: PageShellMaxWidth;
  padded?: boolean;
};

/**
 * Standard page container for app routes — replaces scattered `mx-auto max-w-* p-6` copies.
 */
export function PageShell({
  children,
  className,
  maxWidth = "6xl",
  padded = true,
}: PageShellProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full",
        maxWidthClass[maxWidth],
        padded && "p-6",
        className,
      )}
    >
      {children}
    </div>
  );
}
