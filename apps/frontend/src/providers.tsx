"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import { ensureI18n } from "@/shared/i18n/config";
import { useLanguageStore } from "@/shared/i18n/use-language";

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
  const language = useLanguageStore((state) => state.language);

  useEffect(() => {
    void ensureI18n();
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
    void ensureI18n().then((instance) => {
      if (instance.language !== language) {
        void instance.changeLanguage(language);
      }
    });
  }, [language]);

  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={client}>
        {children}
        <Toaster
          position="top-right"
          richColors={false}
          closeButton={false}
          hotkey={[]}
          containerAriaLabel="Application notifications"
        />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
