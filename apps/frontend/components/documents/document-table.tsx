"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Skeleton } from "@/components/ui/skeleton";
import { DocumentStatusBadge } from "@/components/documents/status-badges";
import { listDocuments } from "@/lib/api/documents";
import { queryKeys } from "@/lib/query/keys";
import { EmptyPanel } from "@/components/layout/empty-panel";
import { formatDateTime } from "@/lib/utils";
import { useI18n } from "@/src/shared/i18n/use-language";

export function DocumentTable() {
  const { t } = useI18n();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
    refetchInterval: 5000,
  });

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return (
      <p className="text-sm text-destructive">{t.common.failedToLoadDocuments}</p>
    );
  if (!data || data.length === 0) {
    return <EmptyPanel description={t.common.noDocumentsYet} />;
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t.common.title}</TableHead>
            <TableHead>{t.common.type}</TableHead>
            <TableHead>{t.common.status}</TableHead>
            <TableHead className="text-right">{t.common.chunks}</TableHead>
            <TableHead>{t.common.updated}</TableHead>
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
