"use client";

import { useEffect, useState } from "react";
import { formatDateTime } from "@/shared/utils";

type TimeProps = {
  value?: string | null;
  className?: string;
};

/**
 * Renders a deterministic UTC label on SSR/first paint, then local locale after mount
 * to avoid React hydration mismatches.
 */
export function Time({ value, className }: TimeProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!value) {
    return <span className={className}>—</span>;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return <span className={className}>—</span>;
  }

  return (
    <time dateTime={date.toISOString()} className={className} suppressHydrationWarning>
      {mounted ? date.toLocaleString() : formatDateTime(value)}
    </time>
  );
}
