"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { EvidenceItemViewModel } from "@/entities/evidence/types";
import { useI18n } from "@/shared/i18n/use-language";
import { track } from "@/shared/telemetry/track";

export function EvidenceDetailDrawer({
  item,
  onClose,
}: {
  item: EvidenceItemViewModel | null;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const sourceLabels: Record<EvidenceItemViewModel["sourceType"], string> = {
    retrieval_citation: t.evidenceDetail.retrievalCitation,
    document_chunk: t.evidenceDetail.documentChunk,
    ontology_candidate_entity: t.evidenceDetail.ontologyCandidateEntity,
    ontology_candidate_relation: t.evidenceDetail.ontologyCandidateRelation,
  };

  return (
    <Sheet open={Boolean(item)} onOpenChange={(open) => !open && onClose()}>
      <SheetContent
        side="right"
        className="flex flex-col gap-4 sm:max-w-lg"
        closeLabel={t.common.accessibility.closeSheet}
      >
        {item && (
          <>
            <SheetHeader>
              <SheetTitle className="text-base">{item.title}</SheetTitle>
              <SheetDescription>{sourceLabels[item.sourceType]}</SheetDescription>
            </SheetHeader>
            <div className="flex flex-wrap gap-2">
              {typeof item.score === "number" && (
                <Badge variant="outline">
                  {t.evidenceDetail.scorePrefix} {formatScore(item.score)}
                </Badge>
              )}
              {typeof item.trustScore === "number" && item.trustScore !== item.score && (
                <Badge variant="outline">
                  {t.evidenceDetail.trustPrefix} {formatScore(item.trustScore)}
                </Badge>
              )}
              {item.citationLabel && <Badge variant="secondary">{item.citationLabel}</Badge>}
            </div>
            {item.contentSnippet && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {t.evidenceDetail.snippet}
                </div>
                <p className="rounded-md border bg-muted/30 p-3 text-sm">{item.contentSnippet}</p>
              </section>
            )}
            {item.provenanceSummary && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {t.evidenceDetail.provenance}
                </div>
                <p className="text-sm">{item.provenanceSummary}</p>
              </section>
            )}
            <section className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t.evidenceDetail.links}
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
                      {t.evidenceDetail.openDocument}
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
                      {t.evidenceDetail.openBuild}
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
                      {t.evidenceDetail.externalSource}
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
