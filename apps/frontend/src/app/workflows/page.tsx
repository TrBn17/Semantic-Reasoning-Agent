"use client";

import { WorkflowRegistryView } from "@/components/workflows/workflow-registry-view";
import { useI18n } from "@/shared/i18n/use-language";

export default function WorkflowsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">{t.pages.workflows.title}</h1>
        <p className="text-sm text-muted-foreground">{t.pages.workflows.description}</p>
      </div>
      <WorkflowRegistryView />
    </div>
  );
}
