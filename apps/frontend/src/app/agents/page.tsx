import { AgentSettingsView } from "@/components/agents/agent-settings-view";

export default function AgentsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Agents</h1>
        <p className="text-sm text-muted-foreground">
          Configure provider env, inspect model metadata, and assign models by
          task to prepare for agent-style workflows.
        </p>
      </div>
      <AgentSettingsView />
    </div>
  );
}
