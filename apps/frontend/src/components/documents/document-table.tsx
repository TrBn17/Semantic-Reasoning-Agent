"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { DocumentStatusBadge } from "@/components/documents/status-badges";
import { listDocuments } from "@/shared/api/documents";
import { Time } from "@/shared/components/time";
import { useI18n } from "@/shared/i18n/use-language";
import { useWorkspaceStore } from "@/shared/state/workspace-store";

export function DocumentTable() {
  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["documents", "list", workspaceId ?? null],
    queryFn: () => listDocuments(workspaceId),
    refetchInterval: 5000,
  });
  const documents = useMemo(() => data ?? [], [data]);
  const rows = useMemo(
    () =>
      documents.filter((doc) => {
        if (statusFilter !== "all" && doc.status !== statusFilter) return false;
        if (!search.trim()) return true;
        return `${doc.title} ${doc.filename} ${doc.document_type}`
          .toLowerCase()
          .includes(search.trim().toLowerCase());
      }),
    [documents, search, statusFilter],
  );

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (isError)
    return (
      <p className="text-sm text-destructive">{t.documents.loadError}</p>
    );
  if (!documents.length)
    return (
      <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
        {t.documents.emptyTable}
      </p>
    );
  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t.common.search} />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="sm:w-44">
            <SelectValue placeholder={t.documents.table.status} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="uploaded">uploaded</SelectItem>
            <SelectItem value="parsed">parsed</SelectItem>
            <SelectItem value="indexed">indexed</SelectItem>
            <SelectItem value="failed">failed</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {rows.length === 0 ? (
        <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
          {t.common.noMatches}
        </p>
      ) : (
      <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t.documents.table.title}</TableHead>
            <TableHead>{t.documents.table.type}</TableHead>
            <TableHead>{t.documents.table.status}</TableHead>
            <TableHead className="text-right">{t.documents.table.chunks}</TableHead>
            <TableHead>{t.documents.table.updated}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((doc) => (
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
                <Time value={doc.updated_at} className="inline" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      </div>
      )}
    </div>
  );
}
