"use client";

import { WorkspaceBadge } from "@/components/layout/workspace-badge";

export function AppHeader({ title }: { title?: string }) {
  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b bg-background px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-medium text-muted-foreground">
          {title ?? "Semantic Reasoning Agent"}
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <WorkspaceBadge />
      </div>
    </header>
  );
}
