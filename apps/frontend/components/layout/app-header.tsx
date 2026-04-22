"use client";

import Image from "next/image";
import { WorkspaceSwitcher } from "@/components/layout/workspace-switcher";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { useI18n } from "@/src/shared/i18n/use-language";

export function AppHeader({ title }: { title?: string }) {
  const { t } = useI18n();

  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b bg-background px-6">
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border bg-slate-100 shadow-sm dark:bg-slate-800/80">
          <Image
            src="/logo.svg"
            alt="Semantic Agent logo"
            width={18}
            height={18}
            className="object-contain"
            priority
          />
        </div>
        <h1 className="text-sm font-medium text-muted-foreground">
          {title ?? t.appName}
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <LanguageSwitcher />
        <WorkspaceSwitcher />
      </div>
    </header>
  );
}
