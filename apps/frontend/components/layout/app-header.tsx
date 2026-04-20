"use client";

import Image from "next/image";
import { WorkspaceBadge } from "@/components/layout/workspace-badge";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useI18n } from "@/src/shared/i18n/use-language";

export function AppHeader({ title }: { title?: string }) {
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-border/70 bg-background/80 px-6 backdrop-blur">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl border bg-gradient-to-br from-primary/15 to-primary/5 shadow-sm ring-1 ring-white/50 dark:ring-white/5">
          <Image
            src="/logo.svg"
            alt={t.layout.logoAlt}
            width={20}
            height={20}
            className="object-contain"
            priority
          />
        </div>
        <div className="leading-tight">
          <p className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
            {t.layout.brandTagline}
          </p>
          <h1 className="text-sm font-semibold text-foreground">
            {title ?? t.appName}
          </h1>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <WorkspaceBadge />
      </div>
    </header>
  );
}
