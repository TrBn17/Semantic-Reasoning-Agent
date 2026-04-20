"use client";

import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  FileText,
  MessageSquare,
  Network,
  Search,
  Sparkles,
} from "lucide-react";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listConversations } from "@/lib/api/conversations";
import { listDocuments } from "@/lib/api/documents";
import { getGraph } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";
import { formatDateTime } from "@/lib/utils";
import { useI18n } from "@/src/shared/i18n/use-language";

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
  const recentConversations = (conversations.data ?? [])
    .slice()
    .sort(sortByUpdatedAtDesc)
    .slice(0, 4);

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8 lg:px-8 lg:py-10">
      <section className="hero-panel surface-panel-strong relative overflow-hidden px-6 py-7 lg:px-8 lg:py-8">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:28px_28px] opacity-40" />
        <div className="relative grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.85fr)] lg:items-end">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.22em] text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              {t.home.heroBadge}
            </div>
            <div className="space-y-2">
              <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                {t.home.title}
              </h1>
              <p className="max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
                {t.home.subtitle}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <SummaryPill label={t.home.summary.documents} value={recentDocuments.length} />
            <SummaryPill
              label={t.home.summary.graphEntities}
              value={graph.data?.entities?.length ?? 0}
            />
            <SummaryPill label={t.home.summary.conversations} value={recentConversations.length} />
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickActions.map(({ href, icon: Icon }) => (
          <Link key={href} href={href} className="group">
            <Card className="surface-panel h-full transition-all duration-200 group-hover:-translate-y-0.5 group-hover:border-primary/35 group-hover:shadow-lg">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <span className="rounded-lg bg-primary/10 p-2 text-primary ring-1 ring-primary/10">
                    <Icon className="h-4 w-4" />
                  </span>
                  {translateQuickActionTitle(href, t)}
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
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
        <Card variant="surface">
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
                className="flex items-center justify-between rounded-xl px-3 py-3 text-sm transition-colors hover:bg-accent/60"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{d.title}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {d.document_type} · {formatDateTime(d.updated_at)}
                  </div>
                </div>
                <Badge variant={badgeVariant(d.status)}>{d.status}</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card variant="surface">
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
            {graph.isLoading && <Skeletons count={2} />}
            {!graph.isLoading && !graph.data?.version && (
              <EmptyState text={t.home.empty.builds} />
            )}
            {graph.data?.version && (
              <Link
                href="/ontology/builds"
                className="flex flex-col rounded-xl px-3 py-3 text-sm transition-colors hover:bg-accent/60"
              >
                <div className="font-medium">
                  v{graph.data.version.version_number} · {graph.data.entities.length} entities ·{" "}
                  {graph.data.relations.length} relations
                </div>
                <div className="text-xs text-muted-foreground">
                  {formatDateTime(graph.data.version.created_at)}
                </div>
              </Link>
            )}
          </CardContent>
        </Card>

        <Card variant="surface">
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
                  {graph.data.version.entity_count} entities ·{" "}
                  {graph.data.version.relation_count} relations · published{" "}
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

        <Card variant="surface">
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
                className="block rounded-xl px-3 py-3 text-sm transition-colors hover:bg-accent/60"
              >
                <div className="truncate font-medium">{c.title}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {c.provider} · {c.model} · {formatDateTime(c.updated_at)}
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      </section>

      {!caps.tasksAvailable && (
        <section>
          <Card className="surface-panel border-dashed">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm">{t.home.tasks.title}</CardTitle>
              <Badge variant="secondary" className="ml-2">{t.home.tasks.badge}</Badge>
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

function SummaryPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="surface-panel flex flex-col items-center justify-center px-4 py-4 text-center">
      <div className="text-2xl font-semibold text-foreground">{value}</div>
      <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
    </div>
  );
}

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
  )
    return "default";
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
