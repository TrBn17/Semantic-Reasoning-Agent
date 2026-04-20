"use client";

import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { useI18n } from "@/src/shared/i18n/use-language";

export function CrossBuildReview() {
  const { t } = useI18n();

  return (
    <div className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
      <p>
        {t.knowledgeGraph.crossReview.intro}{" "}
        {t.knowledgeGraph.crossReview.afterCode}{" "}
        <strong>{t.knowledgeGraph.crossReview.extract}</strong> {t.knowledgeGraph.crossReview.or}{" "}
        <strong>{t.knowledgeGraph.crossReview.ingest}</strong> {t.knowledgeGraph.crossReview.onThe}{" "}
        <Link href="/ontology/builds" className="text-primary underline">
          {t.nav.ontology}
        </Link>{" "}
        {t.knowledgeGraph.crossReview.pageThen}{" "}
        <Link href="/graph" className="text-primary underline">
          {t.nav.graph}
        </Link>
        {t.knowledgeGraph.crossReview.end}
      </p>
    </div>
  );
}
