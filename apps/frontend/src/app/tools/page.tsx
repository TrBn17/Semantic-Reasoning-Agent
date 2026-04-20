import { ToolsTable } from "@/components/tools/tools-table";

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Tools</h1>
        <p className="text-sm text-muted-foreground">
          Registered execution primitives per AGENTS.md §9. Invoke directly for
          diagnostics, or wait for the agentic loop (Phase 4) to dispatch them
          from chat.
        </p>
      </div>
      <ToolsTable />
    </div>
  );
}
