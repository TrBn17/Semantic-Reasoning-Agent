"use client";

import { getCapabilities, type Capabilities } from "./capabilities";

export function useCapabilities(): Capabilities {
  return getCapabilities();
}
