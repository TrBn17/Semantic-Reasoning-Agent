"use client";

import { BuildTable } from "@/components/ontology/build-table";
import { IngestFilesDialog } from "@/components/ontology/ingest-files-dialog";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function OntologyBuildsPage() {
  const { t } = useI18n();

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{t.knowledgeGraph.buildsPage.title}</h1>
          <p className="text-sm text-muted-foreground">{t.knowledgeGraph.buildsPage.subtitle}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <IngestFilesDialog />
          <NewBuildDialog />
        </div>
      </div>
      <BuildTable />
    </div>
  );
}
