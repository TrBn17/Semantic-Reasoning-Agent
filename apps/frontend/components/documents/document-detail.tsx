"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
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
import {
  DocumentStatusBadge,
  JobStatusBadge,
} from "@/components/documents/status-badges";
import {
  getDocument,
  listDocumentJobs,
  reprocessDocument,
} from "@/lib/api/documents";
import { queryKeys } from "@/lib/query/keys";
import { formatDateTime } from "@/lib/utils";

export function DocumentDetail({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const { data: doc, isLoading } = useQuery({
    queryKey: queryKeys.documents.detail(documentId),
    queryFn: () => getDocument(documentId),
    refetchInterval: 5000,
  });
  const { data: jobs } = useQuery({
    queryKey: queryKeys.documents.jobs(documentId),
    queryFn: () => listDocumentJobs(documentId),
    refetchInterval: 3000,
  });
  const mutation = useMutation({
    mutationFn: () => reprocessDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.detail(documentId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.jobs(documentId),
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.list() });
      toast.success("Reprocess queued");
    },
    onError: (err) =>
      toast.error(`Reprocess failed: ${(err as Error).message}`),
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!doc)
    return (
      <p className="text-sm text-destructive">Document not found.</p>
    );

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{doc.title}</h1>
            <DocumentStatusBadge status={doc.status} />
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {doc.filename} · {doc.document_type.toUpperCase()} ·{" "}
            {doc.chunk_count} chunks · parser {doc.parser_version}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Created {formatDateTime(doc.created_at)} · Updated{" "}
            {formatDateTime(doc.updated_at)}
          </p>
          {doc.tags.length > 0 && (
            <p className="mt-1 text-xs text-muted-foreground">
              Tags: {doc.tags.join(", ")}
            </p>
          )}
          {doc.error_message && (
            <p className="mt-2 text-sm text-destructive">
              {doc.error_message}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link href="/documents">Back</Link>
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            <RefreshCcw className="h-4 w-4" />
            Reprocess
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Jobs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Finished</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(jobs ?? []).map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-mono text-xs">{job.name}</TableCell>
                  <TableCell>
                    <JobStatusBadge status={job.status} />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDateTime(job.started_at)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDateTime(job.finished_at)}
                  </TableCell>
                  <TableCell className="text-xs text-destructive">
                    {job.error_message ?? "—"}
                  </TableCell>
                </TableRow>
              ))}
              {(jobs ?? []).length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="text-center text-sm text-muted-foreground"
                  >
                    No jobs yet.
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
