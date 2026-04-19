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
import { listConversations } from "@/lib/api/conversations";
import { listDocuments } from "@/lib/api/documents";
import { listBuilds, getGraph } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";
import { formatDateTime } from "@/lib/utils";

type QuickAction = {
  href: string;
  icon: typeof MessageSquare;
  title: string;
  description: string;
};

const quickActions: QuickAction[] = [
  {
    href: "/ask",
    icon: MessageSquare,
    title: "Ask a question",
    description: "Send a grounded query and inspect cited evidence.",
  },
  {
    href: "/documents",
    icon: FileText,
    title: "Upload document",
    description: "Parse and index a document for retrieval and ontology.",
  },
  {
    href: "/evidence",
    icon: Search,
    title: "Browse evidence",
    description: "Review citations, provenance, and source chunks.",
  },
  {
    href: "/ontology/builds",
    icon: Network,
    title: "Review ontology builds",
    description: "Approve candidate entities and publish graph versions.",
  },
];

export function HomeView() {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const caps = useCapabilities();

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
        <h1 className="text-2xl font-semibold tracking-tight">Workspace</h1>
        <p className="text-sm text-muted-foreground">
          Knowledge operations cockpit for ask, documents, evidence, ontology,
          and graph.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickActions.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/50">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  {title}
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">{description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">Recent documents</CardTitle>
            <Link
              href="/documents"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {documents.isLoading && <Skeletons count={3} />}
            {!documents.isLoading && recentDocuments.length === 0 && (
              <EmptyState text="No documents yet. Upload one to get started." />
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
                    {d.document_type} · {formatDateTime(d.updated_at)}
                  </div>
                </div>
                <Badge variant={badgeVariant(d.status)}>{d.status}</Badge>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">Ontology builds</CardTitle>
            <Link
              href="/ontology/builds"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {builds.isLoading && <Skeletons count={3} />}
            {!builds.isLoading && activeBuilds.length === 0 && (
              <EmptyState text="No builds yet. Create one from a document." />
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
                    {b.entity_count} entities · {b.relation_count} relations ·{" "}
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
            <CardTitle className="text-sm">Published graph</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {graph.isLoading && <Skeletons count={2} />}
            {!graph.isLoading && !graph.data?.version && (
              <EmptyState text="No published ontology version yet." />
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
                  Open graph explorer <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm">Recent conversations</CardTitle>
            <Link
              href="/ask"
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              View all
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {conversations.isLoading && <Skeletons count={3} />}
            {!conversations.isLoading && recentConversations.length === 0 && (
              <EmptyState text="No conversations yet." />
            )}
            {recentConversations.map((c) => (
              <Link
                key={c.id}
                href={`/ask/${c.id}`}
                className="block rounded-md px-2 py-2 text-sm hover:bg-accent"
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
          <Card className="border-dashed">
            <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
              <Sparkles className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm">Tasks & workflows</CardTitle>
              <Badge variant="secondary" className="ml-2">
                coming soon
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Task runtime, workflow catalog, and artifact generation will
                surface here once the backend control plane exposes them.
              </p>
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
  )
    return "default";
  return "secondary";
}

function EmptyState({ text }: { text: string }) {
  return <p className="px-2 py-3 text-xs text-muted-foreground">{text}</p>;
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
