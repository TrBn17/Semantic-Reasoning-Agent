"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  BuildStatusBadge,
  StepStatusBadge,
} from "@/components/ontology/status-badges";
import {
  CandidateEntitiesTable,
  CandidateRelationsTable,
} from "@/components/ontology/candidate-tables";
import { PublishButton } from "@/components/ontology/publish-button";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getBuild } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { formatDateTime } from "@/lib/utils";

export function BuildDetail({ buildId }: { buildId: string }) {
  const { data: build, isLoading } = useQuery({
    queryKey: queryKeys.ontology.build(buildId),
    queryFn: () => getBuild(buildId),
    refetchInterval: 4000,
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!build)
    return <p className="text-sm text-destructive">Build not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-lg">{build.id.slice(0, 8)}…</h1>
            <BuildStatusBadge status={build.status} />
            {build.domain && (
              <span className="rounded bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                {build.domain}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Document{" "}
            <span className="font-mono">{build.document_id.slice(0, 8)}…</span>{" "}
            · Created {formatDateTime(build.created_at)} · Updated{" "}
            {formatDateTime(build.updated_at)}
          </p>
          {build.error_message && (
            <p className="mt-2 text-sm text-destructive">
              {build.error_message}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link href="/ontology/builds">Back</Link>
          </Button>
          <PublishButton build={build} />
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">Entities</p>
            <p className="text-2xl font-semibold">{build.entity_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">
              Pending entities
            </p>
            <p className="text-2xl font-semibold">
              {build.pending_entity_count}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">Relations</p>
            <p className="text-2xl font-semibold">{build.relation_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">
              Pending relations
            </p>
            <p className="text-2xl font-semibold">
              {build.pending_relation_count}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="entities">
        <TabsList>
          <TabsTrigger value="entities">Entities</TabsTrigger>
          <TabsTrigger value="relations">Relations</TabsTrigger>
          <TabsTrigger value="steps">Steps</TabsTrigger>
        </TabsList>
        <TabsContent value="entities" className="space-y-3">
          <CandidateEntitiesTable buildId={build.id} />
        </TabsContent>
        <TabsContent value="relations" className="space-y-3">
          <CandidateRelationsTable buildId={build.id} />
        </TabsContent>
        <TabsContent value="steps">
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Step</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Detail</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Finished</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {build.steps.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono text-xs">
                      {s.name}
                    </TableCell>
                    <TableCell>
                      <StepStatusBadge status={s.status} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {s.detail ?? "—"}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(s.started_at)}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(s.finished_at)}
                    </TableCell>
                  </TableRow>
                ))}
                {build.steps.length === 0 && (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="text-center text-sm text-muted-foreground"
                    >
                      No steps recorded yet.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
