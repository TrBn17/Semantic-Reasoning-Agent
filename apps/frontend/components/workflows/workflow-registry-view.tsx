"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, Rows3, Workflow } from "lucide-react";
import { toast } from "sonner";
import { PageHero } from "@/components/layout/page-hero";
import { PageShell } from "@/components/layout/page-shell";
import { StatTile } from "@/components/layout/stat-tile";
import { EmptyPanel } from "@/components/layout/empty-panel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { listWorkflowRuns, listWorkflows, runWorkflow } from "@/lib/api/workflows";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { cn, formatDateTime } from "@/lib/utils";
import { runStatusBadgeVariant } from "@/lib/badges/run-status";
import { useI18n } from "@/src/shared/i18n/use-language";

export function WorkflowRegistryView() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const workflowsQuery = useQuery({
    queryKey: queryKeys.workflows.list(),
    queryFn: listWorkflows,
  });
  const runsQuery = useQuery({
    queryKey: queryKeys.workflows.runs(),
    queryFn: listWorkflowRuns,
  });

  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string>("");
  const [prompt, setPrompt] = useState(t.workflowsPage.defaultPrompt);
  const [provider, setProvider] = useState("echo");
  const [model, setModel] = useState("local-echo");

  const selectedWorkflow =
    (workflowsQuery.data ?? []).find((workflow) => workflow.workflow_id === selectedWorkflowId) ??
    (workflowsQuery.data ?? [])[0] ??
    null;

  const workflowRuns = useMemo(() => {
    if (!selectedWorkflow) return runsQuery.data ?? [];
    return (runsQuery.data ?? []).filter(
      (run) => run.workflow_id === selectedWorkflow.workflow_id,
    );
  }, [runsQuery.data, selectedWorkflow]);

  const runMutation = useMutation({
    mutationFn: async () => {
      if (!selectedWorkflow) throw new Error(t.workflowsPage.selectWorkflowFirstError);
      if (!workspaceId) throw new Error(t.common.workspaceRequired);
      return runWorkflow(selectedWorkflow.workflow_id, {
        entrypoint: "workflow_console",
        content: prompt,
        workspace_id: workspaceId,
        task_type: "chat",
        requested_output: "answer",
        provider,
        model,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.workflows.runs() });
      await queryClient.invalidateQueries({ queryKey: queryKeys.tasks.list() });
      toast.success(t.workflowsPage.runSubmitted);
    },
    onError: (error) =>
      toast.error(`${t.workflowsPage.runFailedPrefix} ${(error as Error).message}`),
  });

  return (
    <PageShell maxWidth="7xl" className="flex flex-col gap-6 py-8">
      <PageHero
        badge={
          <>
            <Workflow className="h-3.5 w-3.5" />
            {t.workflowsPage.heroBadge}
          </>
        }
        title={t.workflowsPage.title}
        description={t.workflowsPage.subtitle}
        aside={
          <Card className="border-primary/15 bg-background/70 shadow-none">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">{t.workflowsPage.registrySnapshot}</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              <StatTile
                size="sm"
                label={t.workflowsPage.registered}
                value={(workflowsQuery.data ?? []).length}
              />
              <StatTile size="sm" label={t.workflowsPage.runs} value={(runsQuery.data ?? []).length} />
            </CardContent>
          </Card>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_360px]">
        <Card variant="surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">{t.workflowsPage.registryTitle}</CardTitle>
            <CardDescription>{t.workflowsPage.registryDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {workflowsQuery.isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-24 w-full rounded-2xl" />
                ))}
              </div>
            ) : (
              (workflowsQuery.data ?? []).map((workflow) => (
                <button
                  key={workflow.workflow_id}
                  type="button"
                  onClick={() => setSelectedWorkflowId(workflow.workflow_id)}
                  className={cn(
                    "w-full rounded-2xl border px-4 py-4 text-left transition-all",
                    selectedWorkflow?.workflow_id === workflow.workflow_id
                      ? "border-primary/35 bg-primary/5 shadow-sm"
                      : "border-border/70 hover:border-primary/20 hover:bg-accent/30",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="font-medium">{workflow.workflow_id}</div>
                      <div className="text-sm text-muted-foreground">{workflow.description}</div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge variant={workflow.mode === "agentic" ? "info" : "secondary"}>
                        {workflow.mode}
                      </Badge>
                      <span className="text-xs text-muted-foreground">v{workflow.version}</span>
                    </div>
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card variant="surface">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{t.workflowsPage.runCardTitle}</CardTitle>
              <CardDescription>{t.workflowsPage.runCardDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl border border-border/70 bg-muted/20 px-4 py-3 text-sm">
                <div className="font-medium">
                  {selectedWorkflow?.workflow_id ?? t.workflowsPage.noWorkflowSelected}
                </div>
                <div className="mt-1 text-muted-foreground">
                  {selectedWorkflow?.description ?? t.workflowsPage.pickWorkflowFirst}
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="workflow-prompt">{t.workflowsPage.prompt}</Label>
                <Textarea
                  id="workflow-prompt"
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  className="min-h-28"
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="grid gap-2">
                  <Label htmlFor="workflow-provider">{t.workflowsPage.provider}</Label>
                  <Input
                    id="workflow-provider"
                    value={provider}
                    onChange={(event) => setProvider(event.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="workflow-model">{t.workflowsPage.model}</Label>
                  <Input
                    id="workflow-model"
                    value={model}
                    onChange={(event) => setModel(event.target.value)}
                  />
                </div>
              </div>
              <Button
                onClick={() => runMutation.mutate()}
                disabled={runMutation.isPending || !selectedWorkflow}
              >
                <Play className="h-4 w-4" />
                {t.workflowsPage.runButton}
              </Button>
            </CardContent>
          </Card>

          <Card variant="surface">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Rows3 className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">{t.workflowsPage.recentRuns}</CardTitle>
              </div>
              <CardDescription>{t.workflowsPage.recentRunsDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {runsQuery.isLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, index) => (
                    <Skeleton key={index} className="h-16 w-full rounded-xl" />
                  ))}
                </div>
              ) : workflowRuns.length === 0 ? (
                <EmptyPanel description={t.workflowsPage.noRunsForFilter} />
              ) : (
                workflowRuns.slice(0, 8).map((run) => (
                  <div key={run.id} className="rounded-2xl border border-border/70 px-4 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-medium">{run.workflow_id}</div>
                        <div className="font-mono text-xs text-muted-foreground">{run.id}</div>
                      </div>
                      <Badge variant={runStatusBadgeVariant(run.status)}>
                        {translateRunStatus(run.status, t)}
                      </Badge>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {t.workflowsPage.taskLabel} {run.task_id} · {formatDateTime(run.created_at)}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </PageShell>
  );
}

function translateRunStatus(status: string, t: ReturnType<typeof useI18n>["t"]): string {
  const normalized = status.toLowerCase();
  if (normalized === "pending") return t.tasksPage.statusPending;
  if (normalized === "running") return t.tasksPage.statusRunning;
  if (normalized === "completed") return t.tasksPage.statusCompleted;
  if (normalized === "failed") return t.tasksPage.statusFailed;
  return status;
}
