"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getGraph } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export function GraphStats() {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });

  if (isLoading) return <Skeleton className="h-40 w-full" />;
  if (isError || !data)
    return (
      <p className="text-sm text-destructive">Failed to load graph.</p>
    );

  const entities = data.entities ?? [];
  const relations = data.relations ?? [];
  const version = data.version;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              Published entities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{entities.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              Published relations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{relations.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              Latest version
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">
              {version ? `v${version.version_number}` : "—"}
            </p>
            {version && (
              <p className="text-xs text-muted-foreground">
                build {version.source_build_id.slice(0, 8)}…
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Entities</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Aliases</TableHead>
                <TableHead>Source doc</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entities.slice(0, 20).map((e) => (
                <TableRow key={e.id}>
                  <TableCell className="font-medium">{e.name}</TableCell>
                  <TableCell className="text-xs uppercase text-muted-foreground">
                    {e.entity_type}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {e.aliases.join(", ") || "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {e.source_document_id.slice(0, 8)}…
                  </TableCell>
                </TableRow>
              ))}
              {entities.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center text-sm text-muted-foreground"
                  >
                    No published entities yet. Build and publish an ontology from
                    the Builds tab.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
