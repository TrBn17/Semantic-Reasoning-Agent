import { AgentSettingsView } from "@/components/agents/agent-settings-view";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Workspace-level configuration for providers, task model assignment,
          and default profile behavior.
        </p>
      </div>
      <AgentSettingsView />
    </div>
  );
}
