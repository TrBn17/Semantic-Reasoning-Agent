"use client";

import { toast } from "sonner";

function toMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  if (typeof error === "string" && error.trim()) {
    return error;
  }
  return fallback;
}

export const notify = {
  success(message: string) {
    toast.success(message);
  },
  error(error: unknown, fallback: string) {
    toast.error(toMessage(error, fallback));
  },
  warning(message: string) {
    toast.warning(message);
  },
  info(message: string) {
    toast.info(message);
  },
};
