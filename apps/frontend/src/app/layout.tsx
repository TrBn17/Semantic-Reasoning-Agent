import type { Metadata } from "next";
import { cookies } from "next/headers";
import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { IdlePrefetcher } from "@/components/layout/idle-prefetcher";
import { Providers } from "@/src/providers";
import { LOCALE_COOKIE_NAME, normalizeLanguage } from "@/src/shared/i18n/locale";
import "@/src/globals.css";

export const metadata: Metadata = {
  title: "Semantic Reasoning Agent",
  description:
    "ChatGPT-style workspace for multi-LLM chat, RAG, and ontology graph review.",
  icons: {
    icon: [
      { url: "/logo-badge.svg", type: "image/svg+xml" },
      { url: "/logo.svg", type: "image/svg+xml" },
    ],
    shortcut: ["/logo-badge.svg"],
    apple: [{ url: "/logo-badge.svg" }],
  },
  themeColor: "#111827",
};

export default async function AppLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const language = normalizeLanguage(cookieStore.get(LOCALE_COOKIE_NAME)?.value);

  return (
    <html lang={language} suppressHydrationWarning>
      <body suppressHydrationWarning className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <div className="flex min-h-screen w-screen overflow-hidden">
            <AppSidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
              <AppHeader />
              <main className="flex-1 overflow-y-auto bg-transparent">
                {children}
              </main>
            </div>
          </div>
          <IdlePrefetcher />
        </Providers>
      </body>
    </html>
  );
}
