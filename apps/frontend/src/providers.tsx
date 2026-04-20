"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { RouteTransitionProvider } from "@/components/layout/route-transition-provider";
import { Toaster } from "@/components/ui/sonner";

/** `lang` is set on `<html>` in `layout.tsx` (SSR cookie) and updated via `syncBrowserLanguage` in `use-language`. */

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <RouteTransitionProvider>
        {children}
        <Toaster richColors position="top-right" />
      </RouteTransitionProvider>
    </QueryClientProvider>
  );
}
