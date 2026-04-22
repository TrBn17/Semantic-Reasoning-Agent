"use client";

import { ToolsTable } from "@/components/tools/tools-table";
import { useI18n } from "@/shared/i18n/use-language";

export default function ToolsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.pages.tools.title}</h1>
        <p className="text-sm text-muted-foreground">{t.pages.tools.description}</p>
      </div>
      <ToolsTable />
    </div>
  );
}
