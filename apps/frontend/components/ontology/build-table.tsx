"use client";

import { useQuery } from "@tanstack/react-query";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getGraph } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { formatDateTime } from "@/lib/utils";
import { useI18n } from "@/src/shared/i18n/use-language";

export function BuildTable({ limit: _limit }: { limit?: number }) {
  const { t } = useI18n();
  const kg = t.knowledgeGraph.buildTable;
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });

  if (isLoading) return <Skeleton className="h-48 w-full" />;
  if (isError) return <p className="text-sm text-destructive">{kg.loadFailed}</p>;

  const entities = data?.entities ?? [];
  const relations = data?.relations ?? [];
  const version = data?.version;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{kg.cardTitle}</CardTitle>
          <CardDescription>{kg.cardDescription}</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border bg-muted/30 px-4 py-3">
            <p className="text-xs uppercase text-muted-foreground">{kg.metricEntities}</p>
            <p className="text-2xl font-semibold">{entities.length}</p>
          </div>
          <div className="rounded-lg border bg-muted/30 px-4 py-3">
            <p className="text-xs uppercase text-muted-foreground">{kg.metricRelations}</p>
            <p className="text-2xl font-semibold">{relations.length}</p>
          </div>
          <div className="rounded-lg border bg-muted/30 px-4 py-3">
            <p className="text-xs uppercase text-muted-foreground">{kg.metricVersion}</p>
            <p className="text-2xl font-semibold">
              {version ? `v${version.version_number}` : "—"}
            </p>
            {version && (
              <p className="text-xs text-muted-foreground">
                {formatDateTime(version.created_at)}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
      <p className="text-xs text-muted-foreground">
        {kg.footerBeforeLink}
        <Link href="/graph" className="text-primary underline">
          {kg.graphExplorerLink}
        </Link>
        {kg.footerAfterLink}
      </p>
    </div>
  );
}
