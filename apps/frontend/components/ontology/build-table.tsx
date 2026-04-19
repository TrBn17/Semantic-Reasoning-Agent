"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
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
import { listBuilds } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { formatDateTime } from "@/lib/utils";

export function BuildTable({ limit }: { limit?: number }) {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
  });

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
            <TableHead className="text-right">Entities</TableHead>
            <TableHead className="text-right">Relations</TableHead>
            <TableHead className="text-right">Pending</TableHead>
            <TableHead>Updated</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((b) => (
            <TableRow key={b.id}>
              <TableCell>
                <Link
                  href={`/ontology/builds/${b.id}`}
                  className="font-mono text-xs underline-offset-4 hover:underline"
                >
                  {b.id.slice(0, 8)}…
                </Link>
                <div className="text-xs text-muted-foreground">
                  doc {b.document_id.slice(0, 8)}…
                </div>
              </TableCell>
              <TableCell>
                <BuildStatusBadge status={b.status} />
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {b.domain ?? "—"}
              </TableCell>
              <TableCell className="text-right font-mono">
                {b.entity_count}
              </TableCell>
              <TableCell className="text-right font-mono">
                {b.relation_count}
              </TableCell>
              <TableCell className="text-right font-mono">
                {b.pending_entity_count + b.pending_relation_count}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {formatDateTime(b.updated_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
