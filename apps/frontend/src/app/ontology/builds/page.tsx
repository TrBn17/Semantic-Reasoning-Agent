"use client";

import { BuildTable } from "@/components/ontology/build-table";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";
import { useI18n } from "@/shared/i18n/use-language";

export default function OntologyBuildsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{t.pages.ontologyBuilds.title}</h1>
          <p className="text-sm text-muted-foreground">{t.pages.ontologyBuilds.description}</p>
        </div>
        <NewBuildDialog />
      </div>
      <BuildTable />
    </div>
  );
}
