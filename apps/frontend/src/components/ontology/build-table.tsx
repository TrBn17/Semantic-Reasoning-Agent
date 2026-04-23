"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BuildStatusBadge } from "@/components/ontology/status-badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteBuild, listBuilds } from "@/shared/api/ontology";
import { Time } from "@/shared/components/time";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { formatDateTime } from "@/shared/utils";
import { rankItems } from "@/shared/utils/fuzzy";

const STATUS_FILTERS = ["all", "pending", "running", "failed", "published"] as const;

export function BuildTable({ limit }: { limit?: number }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<(typeof STATUS_FILTERS)[number]>("all");
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const previousStatusesRef = useRef<Record<string, string>>({});

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
    refetchInterval: (query) => {
      const builds = query.state.data ?? [];
      return builds.some((build) => build.status === "pending" || build.status === "running")
        ? 4000
        : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (buildId: string) => deleteBuild(buildId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.builds(workspaceId ?? undefined) });
      toast.success("Deleted failed ontology build.");
    },
    onError: (err) => {
      toast.error(`Failed to delete build: ${(err as Error).message}`);
    },
  });

  const builds = useMemo(() => data ?? [], [data]);
  const rows = useMemo(() => {
    const scoped = builds.filter((build) => statusFilter === "all" || build.status === statusFilter);
    const filtered = search.trim()
      ? rankItems(scoped, search, (build) => [
          build.extraction_provider ?? build.provider,
          build.extraction_model ?? build.model,
          build.id,
          build.document_id,
          build.domain,
          build.status,
          build.error_message,
          build.ontology_title,
          formatDateTime(build.created_at),
          formatDateTime(build.updated_at),
        ]).map(({ item }) => item)
      : scoped;
    return limit ? filtered.slice(0, limit) : filtered;
  }, [builds, limit, search, statusFilter]);

  useEffect(() => {
    if (!builds.length) return;

    const previousStatuses = previousStatusesRef.current;
    for (const build of builds) {
      const previousStatus = previousStatuses[build.id];
      if (
        previousStatus &&
        (previousStatus === "pending" || previousStatus === "running") &&
        build.status === "failed"
      ) {
        toast.error(
          `Ontology build ${build.id.slice(0, 8)} failed: ${build.error_message ?? t.ontologyUi.unknownError}`,
        );
      }
    }

    previousStatusesRef.current = Object.fromEntries(builds.map((build) => [build.id, build.status]));
  }, [builds, t.ontologyUi.unknownError]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError) {
    return <p className="text-sm text-destructive">{t.ontologyUi.failedToLoadBuilds}</p>;
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3 rounded-2xl border bg-card p-4">
        <Input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder={t.common.search}
        />
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((filter) => {
            const active = statusFilter === filter;
            return (
              <Button
                key={filter}
                type="button"
                size="sm"
                variant={active ? "default" : "outline"}
                className="rounded-full"
                onClick={() => setStatusFilter(filter)}
              >
                {filter}
              </Button>
            );
          })}
        </div>
      </div>

      {rows.length === 0 ? (
        <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
          {t.ontologyBuild.emptyBuildsList}
        </p>
      ) : (
        <div className="space-y-3">
          {rows.map((build) => {
            const provider = build.extraction_provider ?? build.provider;
            const model = build.extraction_model ?? build.model;
            const pendingCount = build.pending_entity_count + build.pending_relation_count;
            const title =
              build.ontology_title || `${t.ontologyBuild.documentLabel} ${build.document_id.slice(0, 8)}...`;

            return (
              <Card key={build.id} className="overflow-hidden rounded-2xl border">
                <CardContent className="space-y-4 p-4">
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <BuildStatusBadge status={build.status} />
                        {build.domain ? (
                          <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                            {build.domain}
                          </span>
                        ) : null}
                      </div>
                      <div>
                        <Link
                          href={`/ontology/builds/${build.id}`}
                          className="text-base font-semibold underline-offset-4 hover:underline"
                        >
                          {title}
                        </Link>
                        <p className="text-xs text-muted-foreground">
                          #{build.id.slice(0, 8)}... - {provider ?? t.ontologyUi.unknownProvider} /{" "}
                          {model ?? t.ontologyUi.unknownModel}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 self-start">
                      <Button asChild variant="outline" size="sm">
                        <Link href={`/ontology/builds/${build.id}`}>Details</Link>
                      </Button>
                      {build.status === "failed" ? (
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          aria-label={t.common.delete}
                          disabled={deleteMutation.isPending}
                          onClick={() => {
                            const confirmed = window.confirm(
                              `Delete failed ontology build ${build.id.slice(0, 8)}?`,
                            );
                            if (!confirmed) return;
                            deleteMutation.mutate(build.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      ) : null}
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-xl bg-muted/40 px-3 py-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        {t.ontologyBuild.tablePending}
                      </p>
                      <p className="text-lg font-semibold">{pendingCount}</p>
                    </div>
                    <div className="rounded-xl bg-muted/40 px-3 py-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        {t.ontologyBuild.tabEntities}
                      </p>
                      <p className="text-lg font-semibold">{build.entity_count}</p>
                    </div>
                    <div className="rounded-xl bg-muted/40 px-3 py-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        {t.ontologyBuild.tabRelations}
                      </p>
                      <p className="text-lg font-semibold">{build.relation_count}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>
                      {t.ontologyBuild.tableUpdated} <Time value={build.updated_at} className="inline" />
                    </span>
                    {build.status === "failed" && build.error_message ? (
                      <span className="max-w-2xl text-destructive">{build.error_message}</span>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
