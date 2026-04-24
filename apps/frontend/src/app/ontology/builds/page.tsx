"use client";

import { BuildTable } from "@/components/ontology/build-table";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";
import { useI18n } from "@/shared/i18n/use-language";

export default function OntologyBuildsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 py-4 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-2xl border bg-card shadow-sm lg:aspect-video lg:max-h-[calc(100vh-7.5rem)]">
        <div className="flex h-full min-h-0 flex-col p-4 sm:p-5">
          <div className="flex flex-col gap-3 border-b pb-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-xl font-semibold">{t.pages.ontologyBuilds.title}</h1>
            </div>
            <NewBuildDialog />
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto pt-4">
            <BuildTable />
          </div>
        </div>
      </section>
    </div>
  );
}
