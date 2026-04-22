"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { useI18n } from "@/shared/i18n/use-language";

const labelMap: Record<string, keyof ReturnType<typeof useI18n>["t"]["nav"]> = {
  ask: "ask",
  documents: "documents",
  evidence: "evidence",
  ontology: "ontology",
  graph: "graph",
  agents: "agents",
  settings: "settings",
  tools: "tools",
  tasks: "workflows",
  workflows: "workflows",
  connectors: "connectors",
  artifacts: "artifacts",
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const { t } = useI18n();
  const segments = pathname.split("/").filter(Boolean);
  const crumbs = [{ href: "/", label: t.nav.home }].concat(
    segments.map((segment, index) => {
      const href = `/${segments.slice(0, index + 1).join("/")}`;
      const key = labelMap[segment];
      return {
        href,
        label: key ? t.nav[key] : segment,
      };
    }),
  );

  return (
    <div className="hidden items-center gap-1 text-xs text-muted-foreground md:flex">
      {crumbs.map((crumb, index) => (
        <span key={crumb.href} className="inline-flex items-center gap-1">
          {index > 0 ? <ChevronRight className="h-3 w-3" /> : null}
          {index === crumbs.length - 1 ? (
            <span className="font-medium text-foreground">{crumb.label}</span>
          ) : (
            <Link href={crumb.href} className="hover:text-foreground">
              {crumb.label}
            </Link>
          )}
        </span>
      ))}
    </div>
  );
}
