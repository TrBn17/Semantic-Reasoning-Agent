"use client";

import { BuildTable } from "@/components/ontology/build-table";
import { GraphStats } from "@/components/ontology/graph-stats";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function OntologyPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.ontologyPage.title}</h1>
        <p className="text-sm text-muted-foreground">
          {t.ontologyPage.description}
        </p>
      </div>
      <GraphStats />
      <div>
        <h2 className="mb-2 text-sm font-semibold">{t.ontologyPage.recentBuilds}</h2>
        <BuildTable limit={5} />
      </div>
    </div>
  );
}
