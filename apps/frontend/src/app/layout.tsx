import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppHeader } from "@/components/layout/app-header";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { IdlePrefetcher } from "@/components/layout/idle-prefetcher";
import { Providers } from "@/src/providers";
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

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <div className="flex h-screen w-screen overflow-hidden">
            <AppSidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
              <AppHeader />
              <main className="flex-1 overflow-y-auto bg-background">
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
