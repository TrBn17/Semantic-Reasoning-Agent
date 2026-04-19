"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  CandidateEntitiesTable,
  CandidateRelationsTable,
} from "@/components/ontology/candidate-tables";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listBuilds } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export function CrossBuildReview() {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data: builds, isLoading } = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
  });

  const pending = (builds ?? []).filter(
    (b) => b.pending_entity_count + b.pending_relation_count > 0,
  );

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (pending.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No pending candidates across builds.
      </p>
    );

  return (
    <div className="space-y-6">
      {pending.map((b) => (
        <Card key={b.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm">
              <Link
                href={`/ontology/builds/${b.id}`}
                className="font-mono hover:underline"
              >
                Build {b.id.slice(0, 8)}…
              </Link>
            </CardTitle>
            <span className="text-xs text-muted-foreground">
              {b.pending_entity_count} entities · {b.pending_relation_count}{" "}
              relations pending
            </span>
          </CardHeader>
          <CardContent className="space-y-3">
            {b.pending_entity_count > 0 && (
              <CandidateEntitiesTable buildId={b.id} filter="pending_review" />
            )}
            {b.pending_relation_count > 0 && (
              <CandidateRelationsTable buildId={b.id} filter="pending_review" />
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
