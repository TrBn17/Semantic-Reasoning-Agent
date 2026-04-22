"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  ArrowRight,
  FileText,
  MessageSquare,
  Network,
  Search,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listConversations } from "@/shared/api/conversations";
import { listDocuments } from "@/shared/api/documents";
import { getGraph, listBuilds } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import { formatDateTime } from "@/shared/utils";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { useCapabilities } from "@/shared/capabilities/useCapabilities";
import { useI18n } from "@/shared/i18n/use-language";

type QuickAction = {
  href: string;
  icon: typeof MessageSquare;
};

const quickActions: QuickAction[] = [
  {
    href: "/ask",
    icon: MessageSquare,
  },
  {
    href: "/documents",
    icon: FileText,
  },
  {
    href: "/evidence",
    icon: Search,
  },
  {
    href: "/ontology/builds",
    icon: Network,
  },
];

export function HomeView() {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const caps = useCapabilities();
  const { t } = useI18n();

  const documents = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });
  const builds = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
  });
  const graph = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });
  const conversations = useQuery({
    queryKey: queryKeys.conversations.list(),
    queryFn: listConversations,
  });

  const recentDocuments = (documents.data ?? [])
    .slice()
    .sort(sortByUpdatedAtDesc)
    .slice(0, 5);
  const activeBuilds = (builds.data ?? [])
    .slice()
    .sort(sortByUpdatedAtDesc)
    .slice(0, 5);
  const recentConversations = (conversations.data ?? [])
    .slice()
    .sort(sortByUpdatedAtDesc)
    .slice(0, 4);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t.home.title}</h1>
        <p className="text-sm text-muted-foreground">{t.home.subtitle}</p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickActions.map(({ href, icon: Icon }) => (
          <Link key={href} href={href} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/50">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  {translateQuickActionTitle(href, t)}
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  {translateQuickActionDescription(href, t)}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">{t.home.sections.recentDocuments}</CardTitle>
            <Link
              href="/documents"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {t.home.sections.viewAll}
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {documents.isLoading && <Skeletons count={3} />}
            {!documents.isLoading && recentDocuments.length === 0 && (
              <EmptyState text={t.home.empty.documents} />
            )}
            {recentDocuments.map((d) => (
              <Link
                key={d.id}
                href={`/documents/${d.id}`}
                className="flex items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-accent"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{d.title}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {d.document_type} | {formatDateTime(d.updated_at)}
                  </div>
                </div>
                <Badge variant={badgeVariant(d.status)}>{d.status}</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">{t.home.sections.ontologyBuilds}</CardTitle>
            <Link
              href="/ontology/builds"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {t.home.sections.viewAll}
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {builds.isLoading && <Skeletons count={3} />}
            {!builds.isLoading && activeBuilds.length === 0 && (
              <EmptyState text={t.home.empty.builds} />
            )}
            {activeBuilds.map((b) => (
              <Link
                key={b.id}
                href={`/ontology/builds/${b.id}`}
                className="flex items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-accent"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{b.id.slice(0, 8)}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {b.entity_count} {t.common.entities} · {b.relation_count} {t.common.relations} ·{" "}
                    {formatDateTime(b.updated_at)}
                  </div>
                </div>
                <Badge variant={badgeVariant(b.status)}>{b.status}</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">{t.home.sections.publishedGraph}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {graph.isLoading && <Skeletons count={2} />}
            {!graph.isLoading && !graph.data?.version && (
              <EmptyState text={t.home.empty.graph} />
            )}
            {graph.data?.version && (
              <div className="space-y-1">
                <div className="text-lg font-semibold">
                  v{graph.data.version.version_number}
                </div>
                <div className="text-xs text-muted-foreground">
                  {graph.data.version.entity_count} {t.common.entities} ·{" "}
                  {graph.data.version.relation_count} {t.common.relations} · {t.common.published}{" "}
                  {formatDateTime(graph.data.version.created_at)}
                </div>
                <Link
                  href="/graph"
                  className="inline-flex items-center gap-1 pt-2 text-xs text-primary hover:underline"
                >
                  {t.home.openGraphExplorer} <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">{t.home.sections.recentConversations}</CardTitle>
            <Link
              href="/ask"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              {t.home.sections.viewAll}
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {conversations.isLoading && <Skeletons count={3} />}
            {!conversations.isLoading && recentConversations.length === 0 && (
              <EmptyState text={t.home.empty.conversations} />
            )}
            {recentConversations.map((c) => (
              <Link
                key={c.id}
                href={`/ask/${c.id}`}
                className="block rounded-md px-2 py-2 text-sm hover:bg-accent"
              >
                <div className="truncate font-medium">{c.title}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {c.provider} | {c.model} | {formatDateTime(c.updated_at)}
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      </section>

      {!caps.tasksAvailable && (
        <section>
          <Card className="border-dashed">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm">{t.home.tasks.title}</CardTitle>
              <Badge variant="secondary" className="ml-2">
                {t.home.tasks.badge}
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">{t.home.tasks.description}</p>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
}

type WithUpdated = { updated_at: string };

function sortByUpdatedAtDesc<T extends WithUpdated>(a: T, b: T) {
  return b.updated_at.localeCompare(a.updated_at);
}

function badgeVariant(
  status: string,
): "default" | "secondary" | "destructive" | "outline" {
  if (status === "failed") return "destructive";
  if (
    status === "indexed" ||
    status === "completed" ||
    status === "published"
  ) {
    return "default";
  }
  return "secondary";
}

function EmptyState({ text }: { text: string }) {
  return <p className="px-2 py-3 text-xs text-muted-foreground">{text}</p>;
}

function translateQuickActionTitle(href: string, t: ReturnType<typeof useI18n>["t"]) {
  switch (href) {
    case "/ask":
      return t.home.quickActions.ask.title;
    case "/documents":
      return t.home.quickActions.documents.title;
    case "/evidence":
      return t.home.quickActions.evidence.title;
    case "/ontology/builds":
      return t.home.quickActions.ontology.title;
    default:
      return href;
  }
}

function translateQuickActionDescription(
  href: string,
  t: ReturnType<typeof useI18n>["t"],
) {
  switch (href) {
    case "/ask":
      return t.home.quickActions.ask.description;
    case "/documents":
      return t.home.quickActions.documents.description;
    case "/evidence":
      return t.home.quickActions.evidence.description;
    case "/ontology/builds":
      return t.home.quickActions.ontology.description;
    default:
      return href;
  }
}

function Skeletons({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </>
  );
}
