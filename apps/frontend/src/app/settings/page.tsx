"use client";

import { AgentSettingsView } from "@/components/agents/agent-settings-view";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function SettingsPage() {
  const { t } = useI18n();

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.settingsPage.title}</h1>
        <p className="text-sm text-muted-foreground">
          {t.settingsPage.description}
        </p>
      </div>
      <AgentSettingsView />
    </div>
  );
}
