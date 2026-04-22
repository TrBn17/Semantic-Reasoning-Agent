"use client";

import Image from "next/image";
import { WorkspaceSwitcher } from "@/components/layout/workspace-switcher";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/shared/i18n/use-language";
import { Breadcrumbs } from "@/shared/layout/breadcrumbs";
import { MobileNav } from "@/shared/layout/mobile-nav";
import { ThemeToggle } from "@/shared/layout/theme-toggle";
import { UserMenu } from "@/shared/layout/user-menu";

export function AppHeader({ title }: { title?: string }) {
  const { t } = useI18n();

  return (
    <header className="flex h-14 items-center justify-between gap-3 border-b bg-background px-3 md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <MobileNav />
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
        <Breadcrumbs />
      </div>
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" className="hidden md:inline-flex">
          Ctrl/⌘ + K
        </Button>
        <ThemeToggle />
        <LanguageSwitcher />
        <WorkspaceSwitcher />
        <UserMenu />
      </div>
    </header>
  );
}
