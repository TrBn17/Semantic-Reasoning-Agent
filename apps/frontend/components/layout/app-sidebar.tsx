"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Binary,
  Bot,
  FileText,
  MessageSquare,
  Network,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/retrieval", label: "Retrieval", icon: Search },
  { href: "/ontology", label: "Ontology", icon: Network },
  { href: "/ontology/builds", label: "Builds", icon: Binary },
];

export function AppSidebar() {
  const pathname = usePathname();
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
      <nav className="flex-1 space-y-1 p-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active =
            item.href === "/"
              ? pathname === "/"
              : item.href === "/ontology"
                ? pathname === "/ontology" || pathname.startsWith("/ontology/review")
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
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
      </nav>
      <div className="border-t p-3 text-xs text-muted-foreground">
        Phase 3 baseline · chat + docs + ontology
      </div>
    </aside>
  );
}
