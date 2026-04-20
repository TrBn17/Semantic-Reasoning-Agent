"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, ArrowRight, Filter, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listTasks } from "@/lib/api/tasks";
import { queryKeys } from "@/lib/query/keys";
import { formatDateTime } from "@/lib/utils";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { PageHero } from "@/components/layout/page-hero";
import { PageShell } from "@/components/layout/page-shell";
import { StatTile } from "@/components/layout/stat-tile";
import { runStatusBadgeVariant } from "@/lib/badges/run-status";
import { useI18n } from "@/src/shared/i18n/use-language";

export function TaskRunsView() {
  const { t } = useI18n();
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const tasksQuery = useQuery({
    queryKey: queryKeys.tasks.list(),
    queryFn: listTasks,
  });

  const tasks = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    return (tasksQuery.data ?? []).filter((task) => {
      if (statusFilter !== "all" && task.status !== statusFilter) return false;
      if (!keyword) return true;
      return (
        task.id.toLowerCase().includes(keyword) ||
        task.workflow_id?.toLowerCase().includes(keyword) ||
        task.task_type.toLowerCase().includes(keyword)
      );
    });
  }, [searchText, statusFilter, tasksQuery.data]);

  const completed = (tasksQuery.data ?? []).filter((task) => task.status === "completed").length;
  const failed = (tasksQuery.data ?? []).filter((task) => task.status === "failed").length;
  const running = (tasksQuery.data ?? []).filter((task) => task.status === "running").length;

  return (
    <PageShell maxWidth="7xl" className="flex flex-col gap-6 py-8">
      <PageHero
        badge={
          <>
            <Activity className="h-3.5 w-3.5" />
            {t.tasksPage.heroBadge}
          </>
        }
        title={t.tasksPage.title}
        description={t.tasksPage.subtitle}
        aside={
          <div className="grid grid-cols-3 gap-3">
            <StatTile label={t.tasksPage.completed} value={completed} />
            <StatTile label={t.tasksPage.running} value={running} />
            <StatTile label={t.tasksPage.failed} value={failed} />
          </div>
        }
      />

      <Card variant="surface">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base">{t.tasksPage.taskRuns}</CardTitle>
              <CardDescription>{t.tasksPage.taskRunsDescription}</CardDescription>
            </div>
            <div className="flex w-full flex-wrap gap-3 md:w-auto">
              <div className="relative min-w-[220px] flex-1 md:flex-none">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={searchText}
                  onChange={(event) => setSearchText(event.target.value)}
                  placeholder={t.tasksPage.searchPlaceholder}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="min-w-[160px]">
                  <Filter className="mr-2 h-4 w-4 text-muted-foreground" />
                  <SelectValue placeholder={t.tasksPage.filterStatus} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t.tasksPage.statusAll}</SelectItem>
                  <SelectItem value="pending">{t.tasksPage.statusPending}</SelectItem>
                  <SelectItem value="running">{t.tasksPage.statusRunning}</SelectItem>
                  <SelectItem value="completed">{t.tasksPage.statusCompleted}</SelectItem>
                  <SelectItem value="failed">{t.tasksPage.statusFailed}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {tasksQuery.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={index} className="h-14 w-full rounded-xl" />
              ))}
            </div>
          ) : tasks.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/70 bg-muted/20 px-6 py-10 text-center text-sm text-muted-foreground">
              {t.tasksPage.noMatches}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.tasksPage.tableTask}</TableHead>
                  <TableHead>{t.tasksPage.tableStatus}</TableHead>
                  <TableHead>{t.tasksPage.tableWorkflow}</TableHead>
                  <TableHead>{t.tasksPage.tableRuntime}</TableHead>
                  <TableHead>{t.tasksPage.tableUpdated}</TableHead>
                  <TableHead className="text-right">{t.tasksPage.tableDetails}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium">{task.task_type}</div>
                        <div className="font-mono text-xs text-muted-foreground">{task.id}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={runStatusBadgeVariant(task.status)}>
                        {translateRunStatus(task.status, t)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">{task.workflow_id ?? t.tasksPage.unassigned}</div>
                      <div className="text-xs text-muted-foreground">{task.requested_output}</div>
                    </TableCell>
                    <TableCell>
                      <div>{task.provider ?? t.common.na}</div>
                      <div className="text-xs text-muted-foreground">{task.model ?? t.common.na}</div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDateTime(task.updated_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/tasks/${task.id}`} className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
                        {t.tasksPage.openDetails} <ArrowRight className="h-4 w-4" />
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
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
