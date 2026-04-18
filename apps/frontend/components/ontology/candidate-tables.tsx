"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ReviewActions } from "@/components/ontology/review-actions";
import { ReviewStatusBadge } from "@/components/ontology/status-badges";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  listBuildEntities,
  listBuildRelations,
  reviewEntity,
  reviewRelation,
} from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import type { OntologyReviewAction, OntologyReviewStatus } from "@/lib/api/types";

export function CandidateEntitiesTable({
  buildId,
  filter,
}: {
  buildId: string;
  filter?: OntologyReviewStatus;
}) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.ontology.buildEntities(buildId, filter),
    queryFn: () => listBuildEntities(buildId, filter),
    refetchInterval: 4000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ["ontology", "builds", buildId],
    });
    queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
  };

  const mutate = useMutation({
    mutationFn: async (input: { id: string; action: OntologyReviewAction }) =>
      reviewEntity(input.id, { action: input.action }),
    onSuccess: () => {
      invalidate();
      toast.success("Review saved");
    },
    onError: (err) => toast.error(`Failed: ${(err as Error).message}`),
  });

  if (isLoading) return <Skeleton className="h-40 w-full" />;
  const rows = data ?? [];
  if (rows.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No candidate entities{filter ? ` with status ${filter}` : ""}.
      </p>
    );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Confidence</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Evidence</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((e) => (
            <TableRow key={e.id}>
              <TableCell>
                <div className="font-medium">{e.name}</div>
                <div className="text-xs text-muted-foreground">
                  {e.canonical_name}
                  {e.aliases.length > 0 && ` · aliases: ${e.aliases.join(", ")}`}
                </div>
              </TableCell>
              <TableCell className="text-xs uppercase text-muted-foreground">
                {e.entity_type}
              </TableCell>
              <TableCell className="font-mono text-xs">
                {e.confidence.toFixed(3)}
              </TableCell>
              <TableCell>
                <ReviewStatusBadge status={e.status} />
              </TableCell>
              <TableCell className="max-w-md">
                <p className="line-clamp-3 text-xs text-muted-foreground">
                  {e.evidence_text || "—"}
                </p>
              </TableCell>
              <TableCell className="text-right">
                <ReviewActions
                  status={e.status}
                  pending={mutate.isPending}
                  onApprove={() =>
                    mutate.mutate({ id: e.id, action: "approve" })
                  }
                  onReject={() =>
                    mutate.mutate({ id: e.id, action: "reject" })
                  }
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function CandidateRelationsTable({
  buildId,
  filter,
}: {
  buildId: string;
  filter?: OntologyReviewStatus;
}) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.ontology.buildRelations(buildId, filter),
    queryFn: () => listBuildRelations(buildId, filter),
    refetchInterval: 4000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ["ontology", "builds", buildId],
    });
    queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
  };

  const mutate = useMutation({
    mutationFn: async (input: { id: string; action: OntologyReviewAction }) =>
      reviewRelation(input.id, { action: input.action }),
    onSuccess: () => {
      invalidate();
      toast.success("Review saved");
    },
    onError: (err) => toast.error(`Failed: ${(err as Error).message}`),
  });

  if (isLoading) return <Skeleton className="h-40 w-full" />;
  const rows = data ?? [];
  if (rows.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No candidate relations{filter ? ` with status ${filter}` : ""}.
      </p>
    );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>From</TableHead>
            <TableHead>Relation</TableHead>
            <TableHead>To</TableHead>
            <TableHead>Confidence</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Evidence</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.id}>
              <TableCell className="font-medium">{r.source_name}</TableCell>
              <TableCell className="text-xs uppercase text-muted-foreground">
                {r.relation_type}
              </TableCell>
              <TableCell className="font-medium">{r.target_name}</TableCell>
              <TableCell className="font-mono text-xs">
                {r.confidence.toFixed(3)}
              </TableCell>
              <TableCell>
                <ReviewStatusBadge status={r.status} />
              </TableCell>
              <TableCell className="max-w-md">
                <p className="line-clamp-3 text-xs text-muted-foreground">
                  {r.evidence_text || "—"}
                </p>
              </TableCell>
              <TableCell className="text-right">
                <ReviewActions
                  status={r.status}
                  pending={mutate.isPending}
                  onApprove={() =>
                    mutate.mutate({ id: r.id, action: "approve" })
                  }
                  onReject={() =>
                    mutate.mutate({ id: r.id, action: "reject" })
                  }
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
