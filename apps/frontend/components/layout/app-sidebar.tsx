"use client";

import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import {
  Bot,
  Binary,
  FileSearch,
  FileText,
  Home,
  MessageSquare,
  Network,
  Settings,
  Workflow,
  Wrench,
  Package,
  Plug,
  type LucideIcon,
} from "lucide-react";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { cn } from "@/lib/utils";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";
import { useI18n } from "@/src/shared/i18n/use-language";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  available: boolean;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

function buildGroups(
  caps: ReturnType<typeof useCapabilities>,
  t: ReturnType<typeof useI18n>["t"],
): NavGroup[] {
  return [
    {
      label: t.nav.work,
      items: [
        { href: "/", label: t.nav.home, icon: Home, available: true },
        {
          href: "/agents",
          label: t.nav.agents,
          icon: Bot,
          available: caps.agentsAvailable,
        },
        {
          href: "/ask",
          label: t.nav.ask,
          icon: MessageSquare,
          available: caps.askAvailable,
        },
      ],
    },
    {
      label: t.nav.knowledge,
      items: [
        {
          href: "/documents",
          label: t.nav.documents,
          icon: FileText,
          available: caps.documentsAvailable,
        },
        {
          href: "/evidence",
          label: t.nav.evidence,
          icon: FileSearch,
          available: caps.evidenceAvailable,
        },
        {
          href: "/ontology/builds",
          label: t.nav.ontology,
          icon: Binary,
          available: caps.ontologyAvailable,
        },
        {
          href: "/graph",
          label: t.nav.graph,
          icon: Network,
          available: caps.graphAvailable,
        },
      ],
    },
    {
      label: t.nav.automation,
      items: [
        {
          href: "/tasks",
          label: t.nav.tasks,
          icon: Workflow,
          available: caps.tasksAvailable,
        },
        {
          href: "/workflows",
          label: t.nav.workflows,
          icon: Workflow,
          available: caps.workflowsAvailable,
        },
        {
          href: "/tools",
          label: t.nav.tools,
          icon: Wrench,
          available: caps.toolsAvailable,
        },
        {
          href: "/connectors",
          label: t.nav.connectors,
          icon: Plug,
          available: caps.connectorsAvailable,
        },
      ],
    },
    {
      label: t.nav.outputs,
      items: [
        {
          href: "/artifacts",
          label: t.nav.artifacts,
          icon: Package,
          available: caps.artifactsAvailable,
        },
      ],
    },
    {
      label: t.nav.admin,
      items: [
        {
          href: "/settings",
          label: t.nav.settings,
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
  const groups = buildGroups(caps, t).map((g) => ({
    ...g,
    items: g.items.filter((i) => i.available),
  }));

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-border/70 bg-card/70 backdrop-blur">
      <div className="flex h-16 items-center border-b border-border/70 px-4">
        <Link href="/" className="flex items-center gap-3 font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border bg-gradient-to-br from-primary/20 to-primary/5 shadow-sm">
            <Image
              src="/logo.svg"
              alt={t.layout.logoAlt}
              width={18}
              height={18}
              className="object-contain"
              priority
            />
          </div>
          <div className="leading-tight">
            <span className="block truncate text-sm font-semibold text-foreground">{t.appName}</span>
            <span className="block text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {t.layout.controlPlaneLabel}
            </span>
          </div>
        </Link>
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto p-3">
        {groups
          .filter((g) => g.items.length > 0)
          .map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2 text-[11px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
                {group.label}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={`${group.label}:${item.href}:${item.label}`}
                    href={item.href}
                    prefetch
                    onMouseEnter={() => router.prefetch(item.href)}
                    onFocus={() => router.prefetch(item.href)}
                    className={cn(
                        "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200",
                      active
                          ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                      <span className={cn("rounded-lg p-1.5", active ? "bg-white/15" : "bg-background") }>
                        <Icon className="h-4 w-4" />
                      </span>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
      </nav>
      <div className="border-t border-border/70 p-3 text-xs text-muted-foreground">
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
  if (href === "/tasks") {
    return pathname === "/tasks" || pathname.startsWith("/tasks/");
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
