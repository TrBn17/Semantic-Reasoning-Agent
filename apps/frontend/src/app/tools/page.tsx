"use client";

import { PageHero } from "@/components/layout/page-hero";
import { PageShell } from "@/components/layout/page-shell";
import { ToolsTable } from "@/components/tools/tools-table";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function ToolsPage() {
  const { t } = useI18n();

  return (
    <PageShell maxWidth="7xl" className="flex flex-col gap-6 py-8 lg:py-10">
      <PageHero badge={t.toolsPage.heroBadge} title={t.toolsPage.title} description={t.toolsPage.subtitle} />
      <ToolsTable />
    </PageShell>
  );
}
