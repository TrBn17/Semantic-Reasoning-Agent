import { AgentManagementView } from "@/components/agents/agent-management-view";

export default function AgentsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Agents</h1>
        <p className="text-sm text-muted-foreground">
          Manage agent profiles, capability presets, tool policy, knowledge packs, and evidence scope.
        </p>
      </div>
      <AgentManagementView />
    </div>
  );
}
