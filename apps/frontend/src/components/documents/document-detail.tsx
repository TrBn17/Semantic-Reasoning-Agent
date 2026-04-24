"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import Link from "next/link";
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
  listDocumentArtifacts,
  listDocumentJobs,
  reprocessDocument,
} from "@/shared/api/documents";
import { listBuilds } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { Badge } from "@/components/ui/badge";
import { Time } from "@/shared/components/time";
import { notify } from "@/shared/ui/notify";

export function DocumentDetail({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data: doc, isLoading } = useQuery({
    queryKey: queryKeys.documents.detail(documentId),
    queryFn: () => getDocument(documentId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status) return 5000;
      return ["uploaded", "queued", "processing", "running"].includes(status)
        ? 5000
        : false;
    },
  });
  const { data: jobs } = useQuery({
    queryKey: queryKeys.documents.jobs(documentId),
    queryFn: () => listDocumentJobs(documentId),
    refetchInterval: (query) => {
      const rows = query.state.data ?? [];
      if (rows.length === 0) return 3000;
      const hasActiveJob = rows.some((job) =>
        ["pending", "queued", "running", "processing"].includes(job.status),
      );
      return hasActiveJob ? 3000 : false;
    },
  });
  const { data: artifacts } = useQuery({
    queryKey: queryKeys.documents.artifacts(documentId),
    queryFn: () => listDocumentArtifacts(documentId),
  });
  const { data: allBuilds } = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
  });
  const documentBuilds = (allBuilds ?? [])
    .filter((b) => b.document_id === documentId)
    .slice()
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  const markdownArtifact = (artifacts ?? [])
    .filter((artifact) => artifact.artifact_type === "markdown")
    .slice()
    .sort((a, b) => b.created_at.localeCompare(a.created_at))[0];
  const markdownPreview = (() => {
    const inlineText = markdownArtifact?.metadata?.inline_text;
    if (typeof inlineText !== "string") return null;
    const trimmed = inlineText.trim();
    if (!trimmed) return null;
    return trimmed.length > 3000 ? `${trimmed.slice(0, 3000)}\n\n…` : trimmed;
  })();
  const artifactDownloadUrl =
    markdownArtifact?.public_url && /^https?:\/\//.test(markdownArtifact.public_url)
      ? markdownArtifact.public_url
      : null;
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
      notify.success("Reprocess queued");
    },
    onError: (err) => notify.error(`Reprocess failed: ${(err as Error).message}`, "Reprocess failed"),
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!doc)
    return (
      <p className="text-sm text-destructive">Document not found.</p>
    );

  const ingestionMode = String(doc.ingestion_mode ?? "both");

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
            Ingestion mode: {ingestionMode}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Created <Time value={doc.created_at} className="inline" /> · Updated{" "}
            <Time value={doc.updated_at} className="inline" />
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
                    <Time value={job.started_at} className="inline" />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    <Time value={job.finished_at} className="inline" />
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

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm">Extracted markdown</CardTitle>
          {artifactDownloadUrl ? (
            <Button asChild variant="outline" size="sm">
              <a href={artifactDownloadUrl} target="_blank" rel="noreferrer">
                Download
              </a>
            </Button>
          ) : null}
        </CardHeader>
        <CardContent className="space-y-3">
          {!markdownArtifact ? (
            <p className="text-xs text-muted-foreground">No markdown artifact yet.</p>
          ) : (
            <>
              <p className="text-xs text-muted-foreground">
                {markdownArtifact.name} · {markdownArtifact.content_type} · {(markdownArtifact.size_bytes / 1024).toFixed(1)} KB
              </p>
              {artifactDownloadUrl ? null : (
                <p className="text-xs text-amber-700">
                  Download URL is unavailable in this object store mode. Preview uses inline artifact metadata.
                </p>
              )}
              <pre className="max-h-96 overflow-auto rounded-lg border bg-muted/40 p-3 text-xs leading-relaxed whitespace-pre-wrap">
                {markdownPreview ?? "Markdown preview is unavailable for this artifact."}
              </pre>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="text-sm">Ontology builds</CardTitle>
          <Link
            href="/ontology/builds"
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            All builds
          </Link>
        </CardHeader>
        <CardContent className="space-y-2">
          {documentBuilds.length === 0 && (
            <p className="px-2 py-3 text-xs text-muted-foreground">
              No ontology builds for this document yet.
            </p>
          )}
          {documentBuilds.map((b) => (
            <Link
              key={b.id}
              href={`/ontology/builds/${b.id}`}
              className="flex items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-accent"
            >
              <div className="min-w-0">
                <div className="font-mono text-xs">{b.id.slice(0, 12)}</div>
                <div className="truncate text-xs text-muted-foreground">
                  {b.entity_count} entities · {b.relation_count} relations ·{" "}
                  <Time value={b.updated_at} className="inline" />
                </div>
              </div>
              <Badge variant="outline">{b.status}</Badge>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
