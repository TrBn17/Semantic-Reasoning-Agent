"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { toast } from "sonner";
import { EvidenceDetailDrawer } from "@/components/evidence/evidence-detail-drawer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { listBuildEntities, listBuildRelations, listBuilds } from "@/shared/api/ontology";
import { searchRetrieval } from "@/shared/api/retrieval";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import type {
  EvidenceItemViewModel,
  EvidenceSourceType,
} from "@/entities/evidence/types";
import {
  candidateEntityToEvidence,
  candidateRelationToEvidence,
  retrievalResultToEvidence,
} from "@/shared/api/adapters/evidence";
import { useCapabilities } from "@/shared/capabilities/useCapabilities";
import { track } from "@/shared/telemetry/track";

const SOURCE_LABEL: Record<EvidenceSourceType, string> = {
  retrieval_citation: "Retrieval",
  document_chunk: "Document",
  ontology_candidate_entity: "Ontology entity",
  ontology_candidate_relation: "Ontology relation",
};

export function EvidenceView() {
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
    ontology_candidate_entity: true,
    ontology_candidate_relation: true,
  });

  const searchMutation = useMutation({
    mutationFn: (q: string) =>
      searchRetrieval({
        query: q,
        workspace_id: workspaceId ?? undefined,
        top_k: topK,
      }),
    onError: (err) => toast.error(`Search failed: ${(err as Error).message}`),
  });

  const builds = useQuery({
    queryKey: queryKeys.ontology.builds(workspaceId ?? undefined),
    queryFn: () => listBuilds(workspaceId ?? undefined),
    enabled: includeOntology,
  });
  const latestBuild = builds.data?.[0];
  const buildEntities = useQuery({
    queryKey: queryKeys.ontology.buildEntities(latestBuild?.id ?? "none"),
    queryFn: () => listBuildEntities(latestBuild!.id),
    enabled: includeOntology && Boolean(latestBuild),
  });
  const buildRelations = useQuery({
    queryKey: queryKeys.ontology.buildRelations(latestBuild?.id ?? "none"),
    queryFn: () => listBuildRelations(latestBuild!.id),
    enabled: includeOntology && Boolean(latestBuild),
  });

  const items = useMemo(() => {
    const out: EvidenceItemViewModel[] = [];
    if (searchMutation.data) {
      for (const r of searchMutation.data.results) {
        out.push(retrievalResultToEvidence(r));
      }
    }
    if (includeOntology) {
      for (const e of buildEntities.data ?? []) {
        out.push(candidateEntityToEvidence(e));
      }
      for (const r of buildRelations.data ?? []) {
        out.push(candidateRelationToEvidence(r));
      }
    }
    return out.filter((i) => enabledSources[i.sourceType]);
  }, [
    searchMutation.data,
    buildEntities.data,
    buildRelations.data,
    includeOntology,
    enabledSources,
  ]);

  const loading =
    searchMutation.isPending ||
    (includeOntology && (buildEntities.isLoading || buildRelations.isLoading));

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!query.trim()) return;
    track("ask_started", { surface: "evidence", top_k: topK });
    searchMutation.mutate(query.trim());
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Evidence</h1>
        <p className="text-sm text-muted-foreground">
          Search retrieval citations and ontology candidate provenance side by
          side.
        </p>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-3 sm:flex-row">
        <div className="flex flex-1 items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search indexed chunks..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="top_k" className="text-xs text-muted-foreground">
            top_k
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
            Search
          </Button>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-muted/30 px-3 py-2 text-xs">
        <span className="text-muted-foreground">Sources</span>
        {(Object.keys(SOURCE_LABEL) as EvidenceSourceType[]).map((key) => (
          <label key={key} className="flex items-center gap-1.5">
            <input
              type="checkbox"
              className="h-3.5 w-3.5 rounded border-input"
              checked={enabledSources[key]}
              onChange={(e) =>
                setEnabledSources((s) => ({ ...s, [key]: e.target.checked }))
              }
            />
            {SOURCE_LABEL[key]}
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
          Include ontology candidates (latest build)
        </label>
        {!caps.evidencePromotionAvailable && (
          <Badge variant="secondary" className="ml-2">
            promote: coming soon
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
              Run a search or enable ontology candidates to populate evidence.
            </CardContent>
          </Card>
        )}
        {!loading &&
          items.map((item) => (
            <Card
              key={item.id}
              className="cursor-pointer transition-colors hover:border-primary/40"
              onClick={() => {
                setSelected(item);
                track("evidence_panel_opened", {
                  source_type: item.sourceType,
                  item_id: item.id,
                });
              }}
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <CardTitle className="text-sm">{item.title}</CardTitle>
                <div className="flex items-center gap-2">
                  {typeof item.score === "number" && (
                    <Badge variant="outline">{formatScore(item.score)}</Badge>
                  )}
                  <Badge variant="secondary">{SOURCE_LABEL[item.sourceType]}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {item.contentSnippet && (
                  <p className="line-clamp-3 text-xs text-muted-foreground">
                    {item.contentSnippet}
                  </p>
                )}
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  {item.citationLabel && <span>{item.citationLabel}</span>}
                  {item.provenanceSummary && (
                    <span className="text-muted-foreground/70">
                      | {item.provenanceSummary}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
      </section>

      <EvidenceDetailDrawer item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function formatScore(score: number): string {
  if (score > 1) return score.toFixed(2);
  return `${Math.round(score * 100)}%`;
}
