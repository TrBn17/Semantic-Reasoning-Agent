"use client";

import { AgentManagementView } from "@/components/agents/agent-management-view";
import { useI18n } from "@/shared/i18n/use-language";

export default function AgentsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">{t.pages.agents.title}</h1>
        <p className="text-sm text-muted-foreground">{t.pages.agents.description}</p>
      </div>
      <AgentManagementView />
    </div>
  );
}
