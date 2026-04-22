"use client";

import Image from "next/image";
import Link from "next/link";
import { Menu } from "lucide-react";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/shared/utils";
import { useCapabilities } from "@/shared/capabilities/useCapabilities";
import { useI18n } from "@/shared/i18n/use-language";
import { getNavGroups } from "@/components/layout/app-sidebar";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const caps = useCapabilities();
  const { t } = useI18n();
  const groups = getNavGroups(caps).map((group) => ({
    ...group,
    items: group.items.filter((item) => item.available),
  }));

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="lg:hidden">
          <Menu className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 p-0">
        <SheetTitle className="sr-only">{`${t.appName} navigation menu`}</SheetTitle>
        <div className="flex h-14 items-center border-b px-4">
          <Link href="/" className="flex items-center gap-2 font-semibold" onClick={() => setOpen(false)}>
            <div className="flex h-7 w-7 items-center justify-center rounded-md border bg-slate-100 shadow-sm dark:bg-slate-800/80">
              <Image src="/logo.svg" alt={`${t.appName} logo`} width={16} height={16} className="object-contain" priority />
            </div>
            <span>{t.appName}</span>
          </Link>
        </div>
        <nav className="space-y-5 overflow-y-auto p-3">
          {groups.filter((group) => group.items.length > 0).map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t.nav[group.label]}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={`${group.label}:${item.href}`}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {t.nav[item.label]}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
