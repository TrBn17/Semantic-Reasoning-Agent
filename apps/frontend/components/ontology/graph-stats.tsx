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
import { useI18n } from "@/src/shared/i18n/use-language";

export function GraphStats() {
  const { t } = useI18n();
  const gs = t.knowledgeGraph.graphStats;
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });

  if (isLoading) return <Skeleton className="h-40 w-full" />;
  if (isError || !data) return <p className="text-sm text-destructive">{gs.loadFailed}</p>;

  const entities = data.entities ?? [];
  const relations = data.relations ?? [];
  const version = data.version;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              {gs.publishedEntities}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{entities.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              {gs.publishedRelations}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{relations.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase text-muted-foreground">
              {gs.latestVersion}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">
              {version ? `v${version.version_number}` : "—"}
            </p>
            {version && (
              <p className="text-xs text-muted-foreground">
                {gs.buildPrefix} {version.source_build_id.slice(0, 8)}…
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{gs.entitiesSection}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{gs.colName}</TableHead>
                <TableHead>{gs.colType}</TableHead>
                <TableHead>{gs.colAliases}</TableHead>
                <TableHead>{gs.colSourceDoc}</TableHead>
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
                    {gs.emptyEntitiesRow}
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
