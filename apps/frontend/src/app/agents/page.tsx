"use client";

import { AgentSettingsView } from "@/components/agents/agent-settings-view";

export default function AgentsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Agents</h1>
        <p className="text-sm text-muted-foreground">
          Manage operator-facing profiles, prompts, task model routing, and explicit tool binding.
        </p>
      </div>
      <AgentSettingsView />
    </div>
  );
}
