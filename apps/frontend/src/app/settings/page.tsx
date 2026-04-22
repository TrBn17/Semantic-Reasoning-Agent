"use client";

import { ProviderSettingsView } from "@/components/settings/provider-settings-view";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Configure providers, provider readiness, and workspace-level model defaults.
        </p>
      </div>
      <ProviderSettingsView />
    </div>
  );
}
