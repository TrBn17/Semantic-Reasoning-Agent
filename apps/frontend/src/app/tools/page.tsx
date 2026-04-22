import { ToolsTable } from "@/components/tools/tools-table";

export default function ToolsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Admin / Debug Tools</h1>
        <p className="text-sm text-muted-foreground">
          Internal diagnostics for the tool registry and direct tool invocation. This route is no longer part of the primary product workflow.
        </p>
      </div>
      <ToolsTable />
    </div>
  );
}
