"use client";

import { useMutation } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { searchRetrieval } from "@/lib/api/retrieval";
import type { RetrievalSearchResponse } from "@/lib/api/types";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function RetrievalView() {
  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [documentIds, setDocumentIds] = useState("");
  const [result, setResult] = useState<RetrievalSearchResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      searchRetrieval({
        query,
        workspace_id: workspaceId ?? undefined,
        top_k: topK,
        document_ids: documentIds
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      }),
    onSuccess: (res) => setResult(res),
    onError: (err) => toast.error(t.retrieval.searchFailed.replace("{reason}", (err as Error).message)),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.retrieval.title}</h1>
        <p className="text-sm text-muted-foreground">
          {t.retrieval.description}
        </p>
      </div>
      <form onSubmit={onSubmit} className="grid gap-3 rounded-md border p-4">
        <div className="grid gap-1">
          <Label htmlFor="q">{t.retrieval.queryLabel}</Label>
          <Input
            id="q"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.retrieval.queryPlaceholder}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="grid gap-1">
            <Label htmlFor="topk">{t.retrieval.topKLabel}</Label>
            <Input
              id="topk"
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value) || 5)}
            />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="docs">{t.retrieval.docIdsLabel}</Label>
            <Input
              id="docs"
              value={documentIds}
              onChange={(e) => setDocumentIds(e.target.value)}
              placeholder={t.retrieval.docIdsPlaceholder}
            />
          </div>
        </div>
        <div>
          <Button type="submit" disabled={!query.trim() || mutation.isPending}>
            <Search className="h-4 w-4" />
            {t.common.search}
          </Button>
        </div>
      </form>

      {result && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            {result.results.length} {result.results.length === 1 ? t.common.result : t.common.results} for &quot;{result.query}&quot;
          </p>
          {result.results.map((r) => (
            <Card key={r.chunk_id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {r.document_title}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="uppercase">
                    {r.document_type}
                  </Badge>
                  <Badge variant="info">
                    {r.score.toFixed(3)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  {r.citation.location_label}
                </p>
                <p className="mt-2 whitespace-pre-wrap text-sm">{r.excerpt}</p>
              </CardContent>
            </Card>
          ))}
          {result.results.length === 0 && (
            <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
              {t.retrieval.noMatches}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
