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
import { track } from "@/shared/telemetry/track";
import type { EvidenceItemViewModel } from "@/entities/evidence/types";

const SOURCE_LABEL: Record<EvidenceItemViewModel["sourceType"], string> = {
  retrieval_citation: "Retrieval citation",
  document_chunk: "Document chunk",
  ontology_candidate_entity: "Ontology candidate entity",
  ontology_candidate_relation: "Ontology candidate relation",
};

export function EvidenceDetailDrawer({
  item,
  onClose,
}: {
  item: EvidenceItemViewModel | null;
  onClose: () => void;
}) {
  return (
    <Sheet open={Boolean(item)} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex flex-col gap-4 sm:max-w-lg">
        {item && (
          <>
            <SheetHeader>
              <SheetTitle className="text-base">{item.title}</SheetTitle>
              <SheetDescription>
                {SOURCE_LABEL[item.sourceType]}
              </SheetDescription>
            </SheetHeader>
            <div className="flex flex-wrap gap-2">
              {typeof item.score === "number" && (
                <Badge variant="outline">
                  score {formatScore(item.score)}
                </Badge>
              )}
              {typeof item.trustScore === "number" &&
                item.trustScore !== item.score && (
                  <Badge variant="outline">
                    trust {formatScore(item.trustScore)}
                  </Badge>
                )}
              {item.citationLabel && (
                <Badge variant="secondary">{item.citationLabel}</Badge>
              )}
            </div>
            {item.contentSnippet && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Snippet
                </div>
                <p className="rounded-md border bg-muted/30 p-3 text-sm">
                  {item.contentSnippet}
                </p>
              </section>
            )}
            {item.provenanceSummary && (
              <section className="space-y-1">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Provenance
                </div>
                <p className="text-sm">{item.provenanceSummary}</p>
              </section>
            )}
            <section className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Links
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
                      Open document
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
                      Open build
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
                      External source
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
