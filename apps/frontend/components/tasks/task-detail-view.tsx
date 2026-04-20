"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Clock3, Wrench } from "lucide-react";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getTask, listTaskToolCalls } from "@/lib/api/tasks";
import { queryKeys } from "@/lib/query/keys";
import { formatDateTime } from "@/lib/utils";
import { runStatusBadgeVariant } from "@/lib/badges/run-status";
import { useI18n } from "@/src/shared/i18n/use-language";

export function TaskDetailView({ taskId }: { taskId: string }) {
  const { t } = useI18n();
  const taskQuery = useQuery({
    queryKey: queryKeys.tasks.detail(taskId),
    queryFn: () => getTask(taskId),
  });
  const toolCallsQuery = useQuery({
    queryKey: queryKeys.tasks.toolCalls(taskId),
    queryFn: () => listTaskToolCalls(taskId),
  });

  const task = taskQuery.data;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <Link href="/tasks" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            {t.taskDetailPage.backToTasks}
          </Link>
          <h1 className="text-3xl font-semibold tracking-tight">{t.taskDetailPage.title}</h1>
          <p className="font-mono text-xs text-muted-foreground">{taskId}</p>
        </div>
        {task && (
          <Badge variant={runStatusBadgeVariant(task.status)}>
            {translateRunStatus(task.status, t)}
          </Badge>
        )}
      </div>

      {taskQuery.isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      ) : task ? (
        <>
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_320px]">
            <Card variant="surface">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{t.taskDetailPage.runSummaryTitle}</CardTitle>
                <CardDescription>
                  {t.taskDetailPage.runSummaryDescription}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 text-sm md:grid-cols-2">
                <MetaItem label={t.taskDetailPage.metaTaskType} value={task.task_type} />
                <MetaItem label={t.taskDetailPage.metaRequestedOutput} value={task.requested_output} />
                <MetaItem label={t.taskDetailPage.metaWorkflow} value={task.workflow_id ?? t.taskDetailPage.unassigned} />
                <MetaItem label={t.taskDetailPage.metaProvider} value={task.provider ?? t.taskDetailPage.na} />
                <MetaItem label={t.taskDetailPage.metaModel} value={task.model ?? t.taskDetailPage.na} />
                <MetaItem label={t.taskDetailPage.metaUpdated} value={formatDateTime(task.updated_at)} />
              </CardContent>
            </Card>

            <Card variant="surface">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{t.taskDetailPage.outputSnapshotTitle}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {task.error_message ? (
                  <div className="rounded-2xl border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                    <div className="mb-1 inline-flex items-center gap-2 font-medium">
                      <AlertTriangle className="h-4 w-4" />
                      {t.taskDetailPage.errorTitle}
                    </div>
                    <div>{task.error_message}</div>
                  </div>
                ) : null}
                <pre className="max-h-[280px] overflow-auto rounded-2xl border border-border/70 bg-muted/20 p-4 text-xs leading-6 text-muted-foreground">
                  {JSON.stringify(task.output_payload, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>

          <Card variant="surface">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Wrench className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">{t.taskDetailPage.toolCallsTitle}</CardTitle>
              </div>
              <CardDescription>
                {t.taskDetailPage.toolCallsDescription}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {toolCallsQuery.isLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, index) => (
                    <Skeleton key={index} className="h-14 w-full rounded-xl" />
                  ))}
                </div>
              ) : (toolCallsQuery.data ?? []).length === 0 ? (
                <div className="rounded-2xl border border-dashed border-border/70 bg-muted/20 px-6 py-8 text-sm text-muted-foreground">
                  {t.taskDetailPage.noToolCalls}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t.taskDetailPage.colTool}</TableHead>
                      <TableHead>{t.taskDetailPage.colStatus}</TableHead>
                      <TableHead>{t.taskDetailPage.colTrace}</TableHead>
                      <TableHead>{t.taskDetailPage.colLatency}</TableHead>
                      <TableHead>{t.taskDetailPage.colStarted}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(toolCallsQuery.data ?? []).map((toolCall) => (
                      <TableRow key={toolCall.id}>
                        <TableCell>
                          <div className="space-y-1">
                            <div className="font-medium">{toolCall.tool_name}</div>
                            <div className="font-mono text-xs text-muted-foreground">{toolCall.call_id}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={runStatusBadgeVariant(toolCall.status)}>
                            {translateRunStatus(toolCall.status, t)}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {toolCall.trace_id ?? t.taskDetailPage.na}
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center gap-1 text-sm text-muted-foreground">
                            <Clock3 className="h-4 w-4" />
                            {toolCall.latency_ms}ms
                          </span>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {toolCall.started_at ? formatDateTime(toolCall.started_at) : t.taskDetailPage.na}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <Card variant="surface">
          <CardContent className="px-6 py-10 text-sm text-muted-foreground">
            {t.taskDetailPage.taskNotFound}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function translateRunStatus(status: string, t: ReturnType<typeof useI18n>["t"]): string {
  const normalized = status.toLowerCase();
  if (normalized === "pending") return t.tasksPage.statusPending;
  if (normalized === "running") return t.tasksPage.statusRunning;
  if (normalized === "completed") return t.tasksPage.statusCompleted;
  if (normalized === "failed") return t.tasksPage.statusFailed;
  if (normalized === "success") return t.tools.invokeDialog.status.success;
  if (normalized === "partial") return t.tools.invokeDialog.status.partial;
  return status;
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-muted/20 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-2 font-medium">{value}</div>
    </div>
  );
}
