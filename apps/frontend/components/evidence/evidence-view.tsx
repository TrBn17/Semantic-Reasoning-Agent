"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { getGraph } from "@/lib/api/ontology";
import { searchRetrieval } from "@/lib/api/retrieval";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import {
  publishedEntityToEvidence,
  publishedRelationToEvidence,
  retrievalResultToEvidence,
} from "@/src/shared/api/adapters/evidence";
import { useCapabilities } from "@/src/shared/capabilities/useCapabilities";
import { track } from "@/src/shared/telemetry/track";
import { EvidenceDetailDrawer } from "@/components/evidence/evidence-detail-drawer";
import type {
  EvidenceItemViewModel,
  EvidenceSourceType,
} from "@/src/entities/evidence/types";
import { useI18n } from "@/src/shared/i18n/use-language";

export function EvidenceView() {
  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const caps = useCapabilities();
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [selected, setSelected] = useState<EvidenceItemViewModel | null>(null);
  const [includeOntology, setIncludeOntology] = useState(true);
  const [enabledSources, setEnabledSources] = useState<
    Record<EvidenceSourceType, boolean>
  >({
    retrieval_citation: true,
    document_chunk: true,
    ontology_candidate_entity: false,
    ontology_candidate_relation: false,
    ontology_graph_entity: true,
    ontology_graph_relation: true,
  });

  const sourceLabels = useMemo(
    (): Record<EvidenceSourceType, string> => ({
      retrieval_citation: t.evidencePage.sourceLabels.retrieval,
      document_chunk: t.evidencePage.sourceLabels.document,
      ontology_candidate_entity: t.evidencePage.sourceLabels.candidateEntity,
      ontology_candidate_relation: t.evidencePage.sourceLabels.candidateRelation,
      ontology_graph_entity: t.evidencePage.sourceLabels.graphEntity,
      ontology_graph_relation: t.evidencePage.sourceLabels.graphRelation,
    }),
    [t],
  );

  const searchMutation = useMutation({
    mutationFn: (q: string) =>
      searchRetrieval({
        query: q,
        workspace_id: workspaceId ?? undefined,
        top_k: topK,
      }),
    onError: (err) =>
      toast.error(`${t.evidencePage.searchFailedPrefix} ${(err as Error).message}`),
  });

  const graph = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
    enabled: includeOntology,
  });

  const items = useMemo(() => {
    const out: EvidenceItemViewModel[] = [];
    if (searchMutation.data) {
      for (const r of searchMutation.data.results) {
        out.push(retrievalResultToEvidence(r));
      }
    }
    if (includeOntology && graph.data) {
      for (const e of graph.data.entities) {
        out.push(publishedEntityToEvidence(e));
      }
      for (const r of graph.data.relations) {
        out.push(publishedRelationToEvidence(r));
      }
    }
    return out.filter((i) => enabledSources[i.sourceType]);
  }, [searchMutation.data, graph.data, includeOntology, enabledSources]);

  const loading =
    searchMutation.isPending || (includeOntology && graph.isLoading);

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!query.trim()) return;
    track("ask_started", { surface: "evidence", top_k: topK });
    searchMutation.mutate(query.trim());
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t.evidencePage.title}</h1>
        <p className="text-sm text-muted-foreground">{t.evidencePage.subtitle}</p>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
        <div className="flex flex-1 items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t.evidencePage.searchPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="top_k" className="text-xs text-muted-foreground">
            {t.evidencePage.topKLabel}
          </Label>
          <Input
            id="top_k"
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value) || 5)}
            className="h-9 w-20"
          />
          <Button type="submit" disabled={!query.trim() || loading}>
            {t.evidencePage.search}
          </Button>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/30 px-3 py-2 text-xs">
        <span className="text-muted-foreground">{t.evidencePage.sourcesLabel}</span>
        {(Object.keys(sourceLabels) as EvidenceSourceType[]).map((key) => (
          <label key={key} className="flex items-center gap-1.5">
            <input
              type="checkbox"
              className="h-3.5 w-3.5 rounded border-input"
              checked={enabledSources[key]}
              onChange={(e) =>
                setEnabledSources((s) => ({ ...s, [key]: e.target.checked }))
              }
            />
            {sourceLabels[key]}
          </label>
        ))}
        <span className="ml-auto" />
        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            className="h-3.5 w-3.5 rounded border-input"
            checked={includeOntology}
            onChange={(e) => setIncludeOntology(e.target.checked)}
          />
          {t.evidencePage.includeGraph}
        </label>
        {!caps.evidencePromotionAvailable && (
          <Badge variant="secondary" className="ml-2">
            {t.evidencePage.promoteBadge}
          </Badge>
        )}
      </div>

      <section className="space-y-3">
        {loading &&
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        {!loading && items.length === 0 && (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              {t.evidencePage.empty}
            </CardContent>
          </Card>
        )}
        {!loading &&
          items.map((item) => (
            <Card
              key={item.id}
              className="cursor-pointer transition-colors hover:bg-accent/40"
              onClick={() => setSelected(item)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base font-medium">{item.title}</CardTitle>
                  <Badge variant="outline">{sourceLabels[item.sourceType]}</Badge>
                </div>
                {item.summary && (
                  <p className="text-xs text-muted-foreground">{item.summary}</p>
                )}
              </CardHeader>
              <CardContent>
                <p className="line-clamp-3 text-sm text-muted-foreground">
                  {item.contentSnippet ?? item.summary ?? t.evidencePage.emptyPreview}
                </p>
              </CardContent>
            </Card>
          ))}
      </section>

      <EvidenceDetailDrawer item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
