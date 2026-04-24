"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Binary,
  Brain,
  FileText,
  Home,
  MessageSquare,
  Network,
  Bot,
  Settings,
  Workflow,
  Package,
  Plug,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/shared/utils";
import { useCapabilities } from "@/shared/capabilities/useCapabilities";
import { useI18n } from "@/shared/i18n/use-language";

export type NavItem = {
  href: string;
  label: keyof ReturnType<typeof useI18n>["t"]["nav"];
  icon: LucideIcon;
  available: boolean;
};

export type NavGroup = {
  label: "work" | "knowledge" | "automation" | "outputs" | "admin";
  items: NavItem[];
};

export function getNavGroups(caps: ReturnType<typeof useCapabilities>): NavGroup[] {
  return [
    {
      label: "work",
      items: [
        { href: "/", label: "home", icon: Home, available: true },
        {
          href: "/ask",
          label: "ask",
          icon: MessageSquare,
          available: caps.askAvailable,
        },
      ],
    },
    {
      label: "knowledge",
      items: [
        {
          href: "/documents",
          label: "documents",
          icon: FileText,
          available: caps.documentsAvailable,
        },
        {
          href: "/knowledge",
          label: "knowledgePacks",
          icon: Brain,
          available: caps.documentsAvailable,
        },
        {
          href: "/ontology/builds",
          label: "ontology",
          icon: Binary,
          available: caps.ontologyAvailable,
        },
        {
          href: "/graph",
          label: "graph",
          icon: Network,
          available: caps.graphAvailable,
        },
      ],
    },
    {
      label: "automation",
      items: [
        {
          href: "/workflows",
          label: "workflows",
          icon: Workflow,
          available: caps.workflowsAvailable,
        },
        {
          href: "/connectors",
          label: "connectors",
          icon: Plug,
          available: caps.connectorsAvailable,
        },
      ],
    },
    {
      label: "outputs",
      items: [
        {
          href: "/artifacts",
          label: "artifacts",
          icon: Package,
          available: caps.artifactsAvailable,
        },
      ],
    },
    {
      label: "admin",
      items: [
        {
          href: "/agents",
          label: "agents",
          icon: Bot,
          available: caps.settingsAvailable,
        },
        {
          href: "/settings",
          label: "settings",
          icon: Settings,
          available: caps.settingsAvailable,
        },
      ],
    },
  ];
}

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const caps = useCapabilities();
  const { t } = useI18n();
  const groups = getNavGroups(caps).map((g) => ({
    ...g,
    items: g.items.filter((i) => i.available),
  }));

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r bg-muted/30 lg:flex">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded-md border bg-slate-100 shadow-sm dark:bg-slate-800/80">
            <Image
              src="/logo.svg"
              alt={`${t.appName} logo`}
              width={16}
              height={16}
              className="object-contain"
              priority
            />
          </div>
          <span className="truncate">{t.appName}</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto p-3">
        {groups
          .filter((g) => g.items.length > 0)
          .map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t.nav[group.label]}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={`${group.label}:${item.href}:${String(item.label)}`}
                    href={item.href}
                    prefetch
                    onMouseEnter={() => router.prefetch(item.href)}
                    onFocus={() => router.prefetch(item.href)}
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
      <div className="border-t p-3 text-xs text-muted-foreground">
        {t.workspaceControlPlane}
      </div>
    </aside>
  );
}

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  if (href === "/ontology/builds") {
    return (
      pathname === "/ontology" ||
      pathname.startsWith("/ontology/builds") ||
      pathname.startsWith("/ontology/review")
    );
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
