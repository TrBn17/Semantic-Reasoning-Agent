"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { listWorkflows, runWorkflow } from "@/shared/api/workflows";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { notify } from "@/shared/ui/notify";

export function WorkflowRegistryView() {
  const workspaceId = useActiveWorkspaceId();
  const [content, setContent] = useState("Summarize current workspace status.");
  const [result, setResult] = useState<unknown>(null);
  const workflowsQuery = useQuery({
    queryKey: ["workflows", "registry"],
    queryFn: listWorkflows,
  });
  const mutation = useMutation({
    mutationFn: (workflowId: string) =>
      runWorkflow(workflowId, {
        content,
        workspace_id: workspaceId ?? undefined,
      }),
    onSuccess: (data) => {
      setResult(data);
      notify.success("Workflow run completed.");
    },
    onError: (error) => notify.error(`Workflow run failed: ${(error as Error).message}`, "Workflow run failed"),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Workflow registry</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input value={content} onChange={(event) => setContent(event.target.value)} />
          <div className="space-y-2">
            {(workflowsQuery.data ?? []).map((workflow) => (
              <div key={workflow.workflow_id} className="flex items-center justify-between rounded-md border px-3 py-2">
                <div>
                  <div className="font-mono text-sm">{workflow.workflow_id}</div>
                  <div className="text-xs text-muted-foreground">
                    {workflow.mode} · v{workflow.version}
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={() => mutation.mutate(workflow.workflow_id)}
                  disabled={mutation.isPending}
                >
                  Run
                </Button>
              </div>
            ))}
            {(workflowsQuery.data ?? []).length === 0 && (
              <div className="rounded-md border border-dashed px-4 py-6 text-sm text-muted-foreground">
                No workflows exposed by backend.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Workflow result</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-md bg-muted/40 p-3 text-xs">{JSON.stringify(result, null, 2)}</pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
