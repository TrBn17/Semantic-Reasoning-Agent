"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { BuildStatusBadge } from "@/components/ontology/status-badges";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listBuilds } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { formatDateTime } from "@/shared/utils";

export function BuildTable({ limit }: { limit?: number }) {
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

  useEffect(() => {
    if (!data || data.length === 0) return;

    const previousStatuses = previousStatusesRef.current;
    for (const build of data) {
      const previousStatus = previousStatuses[build.id];
      if (
        previousStatus &&
        (previousStatus === "pending" || previousStatus === "running") &&
        build.status === "failed"
      ) {
        toast.error(
          `Ontology build ${build.id.slice(0, 8)} failed: ${build.error_message ?? "Unknown error"}`,
        );
      }
    }

    previousStatusesRef.current = Object.fromEntries(
      data.map((build) => [build.id, build.status]),
    );
  }, [data]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return <p className="text-sm text-destructive">Failed to load builds.</p>;

  const rows = limit ? (data ?? []).slice(0, limit) : data ?? [];
  if (rows.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No ontology builds yet.
      </p>
    );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Build</TableHead>
            <TableHead>Status</TableHead>
              <TableHead>Domain</TableHead>
              <TableHead>Model</TableHead>
              <TableHead className="text-right">Entities</TableHead>
            <TableHead className="text-right">Relations</TableHead>
            <TableHead className="text-right">Pending</TableHead>
            <TableHead>Updated</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((build) => (
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
                {build.model ? `${build.provider ?? "default"} · ${build.model}` : "workspace default"}
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
                {formatDateTime(build.updated_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
