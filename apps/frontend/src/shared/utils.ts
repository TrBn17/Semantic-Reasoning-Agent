import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Stable UTC string for SSR + client (avoids hydration mismatch from `toLocaleString()`). */
const DATE_TIME_UTC_FMT = new Intl.DateTimeFormat("en-GB", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

/** Human-readable duration between two ISO timestamps (for step tables). */
export function formatStepDuration(
  startedAt?: string | null,
  finishedAt?: string | null,
): string {
  if (!startedAt || !finishedAt) return "—";
  const a = new Date(startedAt).getTime();
  const b = new Date(finishedAt).getTime();
  if (Number.isNaN(a) || Number.isNaN(b) || b < a) return "—";
  const ms = b - a;
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)} s`;
  const m = Math.floor(ms / 60_000);
  const s = Math.round((ms % 60_000) / 1000);
  return `${m}m ${s}s`;
}

export function formatDateTime(value: string | undefined | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return `${DATE_TIME_UTC_FMT.format(date)} UTC`;
}
