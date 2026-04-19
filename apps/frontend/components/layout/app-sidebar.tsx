"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Binary,
  Bot,
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
import { cn } from "@/lib/utils";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";

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
          href: "/tools",
          label: "Tools",
          icon: Wrench,
          available: caps.toolsAvailable,
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
          label: "Settings",
          icon: Settings,
          available: caps.settingsAvailable,
        },
        {
          href: "/agents",
          label: "Agent profiles",
          icon: Bot,
          available: caps.settingsAvailable,
        },
      ],
    },
  ];
}

export function AppSidebar() {
  const pathname = usePathname();
  const caps = useCapabilities();
  const groups = buildGroups(caps).map((g) => ({
    ...g,
    items: g.items.filter((i) => i.available),
  }));

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r bg-muted/30">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Network className="h-4 w-4" />
          </div>
          <span className="truncate">Semantic Agent</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto p-3">
        {groups
          .filter((g) => g.items.length > 0)
          .map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {group.label}
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    key={`${group.label}:${item.href}:${item.label}`}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          ))}
      </nav>
      <div className="border-t p-3 text-xs text-muted-foreground">
        Workspace control plane
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
