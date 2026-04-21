"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DocumentStatusBadge } from "@/components/documents/status-badges";
import { listDocuments } from "@/shared/api/documents";
import { queryKeys } from "@/shared/query/keys";
import { formatDateTime } from "@/shared/utils";

export function DocumentTable() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
    refetchInterval: 5000,
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return (
      <p className="text-sm text-destructive">Failed to load documents.</p>
    );
  if (!data || data.length === 0)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        No documents yet. Upload a PDF, DOCX, or XLSX to start.
      </p>
    );

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Chunks</TableHead>
            <TableHead>Updated</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell>
                <Link
                  href={`/documents/${doc.id}`}
                  className="font-medium underline-offset-4 hover:underline"
                >
                  {doc.title}
                </Link>
                <div className="text-xs text-muted-foreground">{doc.filename}</div>
              </TableCell>
              <TableCell className="uppercase">{doc.document_type}</TableCell>
              <TableCell>
                <DocumentStatusBadge status={doc.status} />
              </TableCell>
              <TableCell className="text-right font-mono">
                {doc.chunk_count}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {formatDateTime(doc.updated_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
