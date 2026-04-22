"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { BuildStatusBadge } from "@/components/ontology/status-badges";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { deleteBuild, listBuilds } from "@/shared/api/ontology";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { Time } from "@/shared/components/time";
import { rankItems } from "@/shared/utils/fuzzy";
import { formatDateTime } from "@/shared/utils";

export function BuildTable({ limit }: { limit?: number }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
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
    const scoped = builds.filter((build) => {
      if (statusFilter !== "all" && build.status !== statusFilter) return false;
      return true;
    });
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

    previousStatusesRef.current = Object.fromEntries(
      builds.map((build) => [build.id, build.status]),
    );
  }, [builds, t.ontologyUi.unknownError]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return <p className="text-sm text-destructive">{t.ontologyUi.failedToLoadBuilds}</p>;

  if (rows.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        {t.ontologyBuild.emptyBuildsList}
      </p>
    );

  return (
    <div className="space-y-3">
      <div className="grid gap-2 sm:grid-cols-[1fr_180px]">
        <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t.common.search} />
        <Input
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value || "all")}
          placeholder={t.ontologyBuild.statusFilterPlaceholder}
        />
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t.ontologyBuild.tableBuild}</TableHead>
              <TableHead>{t.ontologyBuild.tableStatus}</TableHead>
              <TableHead>{t.ontologyBuild.tableDomain}</TableHead>
              <TableHead>{t.ontologyBuild.tableModel}</TableHead>
              <TableHead className="text-right">{t.ontologyBuild.tableEntities}</TableHead>
              <TableHead className="text-right">{t.ontologyBuild.tableRelations}</TableHead>
              <TableHead className="text-right">{t.ontologyBuild.tablePending}</TableHead>
              <TableHead>{t.ontologyBuild.tableUpdated}</TableHead>
              <TableHead className="text-right">{t.common.delete}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((build) => {
              const provider = build.extraction_provider ?? build.provider;
              const model = build.extraction_model ?? build.model;
              return (
                <TableRow key={build.id}>
              <TableCell>
                <Link
                  href={`/ontology/builds/${build.id}`}
                  className="font-mono text-xs underline-offset-4 hover:underline"
                >
                  {build.id.slice(0, 8)}...
                </Link>
                <div className="text-xs text-muted-foreground">
                  doc {build.document_id.slice(0, 8)}...
                </div>
                {build.ontology_title ? (
                  <div className="mt-1 text-sm font-medium">{build.ontology_title}</div>
                ) : null}
                {build.status === "failed" && build.error_message && (
                  <div className="mt-1 max-w-sm text-xs text-destructive">
                    {build.error_message}
                  </div>
                )}
              </TableCell>
              <TableCell>
                <BuildStatusBadge status={build.status} />
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {build.domain ?? "-"}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {model ? `${provider ?? t.ontologyUi.unknownProvider} · ${model}` : t.ontologyUi.modelNotRecorded}
              </TableCell>
              <TableCell className="text-right font-mono">
                {build.entity_count}
              </TableCell>
              <TableCell className="text-right font-mono">
                {build.relation_count}
              </TableCell>
              <TableCell className="text-right font-mono">
                {build.pending_entity_count + build.pending_relation_count}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                <Time value={build.updated_at} className="inline" />
              </TableCell>
                  <TableCell className="text-right">
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
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
