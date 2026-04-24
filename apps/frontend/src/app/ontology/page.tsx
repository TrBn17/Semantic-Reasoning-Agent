"use client";

import Link from "next/link";
import { BuildTable } from "@/components/ontology/build-table";
import { GraphStats } from "@/components/ontology/graph-stats";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/shared/i18n/use-language";

export default function OntologyPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{t.pages.ontologyHub.title}</h1>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link href="/graph">{t.pages.ontologyHub.openGraphEditor}</Link>
          </Button>
          <NewBuildDialog />
        </div>
      </div>
      <GraphStats />
      <div>
        <h2 className="mb-2 text-sm font-semibold">{t.pages.ontologyHub.recentBuilds}</h2>
        <BuildTable limit={5} />
      </div>
    </div>
  );
}
