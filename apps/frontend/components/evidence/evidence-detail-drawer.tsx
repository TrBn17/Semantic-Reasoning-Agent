"use client";

import { useMemo } from "react";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { track } from "@/src/shared/telemetry/track";
import type { EvidenceItemViewModel } from "@/src/entities/evidence/types";
import { useI18n } from "@/src/shared/i18n/use-language";

export function EvidenceDetailDrawer({
  item,
  onClose,
}: {
  item: EvidenceItemViewModel | null;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const drawerSourceLabels = useMemo(
    (): Record<EvidenceItemViewModel["sourceType"], string> => ({
      retrieval_citation: t.evidencePage.drawerSourceLabels.retrieval,
      document_chunk: t.evidencePage.drawerSourceLabels.document,
      ontology_candidate_entity: t.evidencePage.drawerSourceLabels.candidateEntity,
      ontology_candidate_relation: t.evidencePage.drawerSourceLabels.candidateRelation,
      ontology_graph_entity: t.evidencePage.drawerSourceLabels.graphEntity,
      ontology_graph_relation: t.evidencePage.drawerSourceLabels.graphRelation,
    }),
    [t],
  );

  return (
    <Sheet open={Boolean(item)} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex flex-col gap-4 sm:max-w-lg">
        {item && (
          <>
            <SheetHeader>
              <SheetTitle className="text-base">{item.title}</SheetTitle>
              <SheetDescription>
                {drawerSourceLabels[item.sourceType]}
              </SheetDescription>
            </SheetHeader>
            <div className="flex flex-wrap gap-2">
              {typeof item.score === "number" && (
                <Badge variant="outline">
                  {t.evidencePage.scoreBadgePrefix} {formatScore(item.score)}
                </Badge>
              )}
              {typeof item.trustScore === "number" &&
                item.trustScore !== item.score && (
                  <Badge variant="outline">
                    {t.evidencePage.trustBadgePrefix} {formatScore(item.trustScore)}
                  </Badge>
                )}
              {item.citationLabel && (
                <Badge variant="secondary">{item.citationLabel}</Badge>
              )}
            </div>
            {item.contentSnippet && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {t.evidencePage.drawerSnippet}
                </div>
                <p className="rounded-md border bg-muted/30 p-3 text-sm">
                  {item.contentSnippet}
                </p>
              </section>
            )}
            {item.provenanceSummary && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {t.evidencePage.drawerProvenance}
                </div>
                <p className="text-sm">{item.provenanceSummary}</p>
              </section>
            )}
            <section className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t.evidencePage.drawerLinks}
              </div>
              <div className="flex flex-wrap gap-2">
                {item.documentId && (
                  <Link href={`/documents/${item.documentId}`}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        track("source_opened", {
                          kind: "document",
                          document_id: item.documentId,
                        })
                      }
                    >
                      {t.evidencePage.openDocument}
                    </Button>
                  </Link>
                )}
                {item.buildId && (
                  <Link href={`/ontology/builds/${item.buildId}`}>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        track("source_opened", {
                          kind: "build",
                          build_id: item.buildId,
                        })
                      }
                    >
                      {t.evidencePage.openBuild}
                    </Button>
                  </Link>
                )}
                {item.uri && (
                  <a href={item.uri} target="_blank" rel="noreferrer">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        track("source_opened", {
                          kind: "external",
                          uri: item.uri,
                        })
                      }
                    >
                      {t.evidencePage.externalSource}
                    </Button>
                  </a>
                )}
              </div>
            </section>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}

function formatScore(score: number): string {
  if (score > 1) return score.toFixed(2);
  return `${Math.round(score * 100)}%`;
}
