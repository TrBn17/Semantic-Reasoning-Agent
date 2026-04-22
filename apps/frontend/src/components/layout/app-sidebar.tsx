"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Binary,
  FileSearch,
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

function buildGroups(caps: ReturnType<typeof useCapabilities>): NavGroup[] {
  return [
    {
      label: "Work",
      items: [
        { href: "/", label: "Home", icon: Home, available: true },
        {
          href: "/ask",
          label: "Ask",
          icon: MessageSquare,
          available: caps.askAvailable,
        },
      ],
    },
    {
      label: "Knowledge",
      items: [
        {
          href: "/documents",
          label: "Documents",
          icon: FileText,
          available: caps.documentsAvailable,
        },
        {
          href: "/evidence",
          label: "Evidence",
          icon: FileSearch,
          available: caps.evidenceAvailable,
        },
        {
          href: "/ontology/builds",
          label: "Ontology",
          icon: Binary,
          available: caps.ontologyAvailable,
        },
        {
          href: "/graph",
          label: "Graph",
          icon: Network,
          available: caps.graphAvailable,
        },
      ],
    },
    {
      label: "Automation",
      items: [
        {
          href: "/workflows",
          label: "Workflows",
          icon: Workflow,
          available: caps.workflowsAvailable,
        },
        {
          href: "/connectors",
          label: "Connectors",
          icon: Plug,
          available: caps.connectorsAvailable,
        },
      ],
    },
    {
      label: "Outputs",
      items: [
        {
          href: "/artifacts",
          label: "Artifacts",
          icon: Package,
          available: caps.artifactsAvailable,
        },
      ],
    },
    {
      label: "Admin",
      items: [
        {
          href: "/agents",
          label: "Agents",
          icon: Bot,
          available: caps.settingsAvailable,
        },
        {
          href: "/settings",
          label: "Settings",
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
  const groups = buildGroups(caps).map((g) => ({
    ...g,
    items: g.items.filter((i) => i.available),
  }));

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r bg-muted/30">
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
                {translateGroupLabel(group.label, t)}
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
                      "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {translateNavLabel(item.label, t)}
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

function translateGroupLabel(label: string, t: ReturnType<typeof useI18n>["t"]) {
  const map: Record<string, string> = {
    Work: t.nav.work,
    Knowledge: t.nav.knowledge,
    Automation: t.nav.automation,
    Outputs: t.nav.outputs,
    Admin: t.nav.admin,
  };
  return map[label] ?? label;
}

function translateNavLabel(label: string, t: ReturnType<typeof useI18n>["t"]) {
  const map: Record<string, string> = {
    Home: t.nav.home,
    Ask: t.nav.ask,
    Documents: t.nav.documents,
    Evidence: t.nav.evidence,
    Ontology: t.nav.ontology,
    Graph: t.nav.graph,
    Agents: "Agents",
    Workflows: t.nav.workflows,
    Connectors: t.nav.connectors,
    Artifacts: t.nav.artifacts,
    Settings: t.nav.settings,
  };
  return map[label] ?? label;
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
