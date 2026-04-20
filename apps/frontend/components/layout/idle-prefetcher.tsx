"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";

const STATIC_ROUTES = ["/", "/ask", "/documents", "/evidence", "/graph"];

type IdleDeadline = { didTimeout: boolean; timeRemaining: () => number };

type IdleWindow = Window & {
  requestIdleCallback?: (cb: (d: IdleDeadline) => void, opts?: { timeout: number }) => number;
  cancelIdleCallback?: (id: number) => void;
};

export function IdlePrefetcher() {
  const router = useRouter();
  const caps = useCapabilities();

  useEffect(() => {
    const routes = [...STATIC_ROUTES];
    if (caps.ontologyAvailable) routes.push("/ontology/builds");
    if (caps.settingsAvailable) routes.push("/settings");

    const w = window as IdleWindow;

    const run = () => {
      for (const href of routes) {
        try {
          router.prefetch(href);
        } catch {
          // ignore prefetch failures (offline, etc.)
        }
      }
    };

    if (typeof w.requestIdleCallback === "function") {
      const id = w.requestIdleCallback(run, { timeout: 2000 });
      return () => w.cancelIdleCallback?.(id);
    }
    const timer = window.setTimeout(run, 1500);
    return () => window.clearTimeout(timer);
  }, [router, caps]);

  return null;
}
