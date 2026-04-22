"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  BuildStatusBadge,
  StepStatusBadge,
} from "@/components/ontology/status-badges";
import {
  CandidateEntitiesTable,
  CandidateRelationsTable,
} from "@/components/ontology/candidate-tables";
import { PublishButton } from "@/components/ontology/publish-button";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Time } from "@/shared/components/time";
import { deleteBuild, getBuild } from "@/shared/api/ontology";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { formatStepDuration } from "@/shared/utils";
import { toast } from "sonner";

export function BuildDetail({ buildId }: { buildId: string }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("entities");
  const { data: build, isLoading } = useQuery({
    queryKey: queryKeys.ontology.build(buildId),
    queryFn: () => getBuild(buildId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 4000 : false;
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => deleteBuild(buildId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.builds() });
      toast.success("Deleted failed ontology build.");
      window.location.href = "/ontology/builds";
    },
    onError: (err) => {
      toast.error(`Failed to delete build: ${(err as Error).message}`);
    },
  });

  const stepsProgress = useMemo(() => {
    if (!build?.steps.length) return { done: 0, total: 0, pct: 0 };
    const total = build.steps.length;
    const done = build.steps.filter((s) => s.status === "completed" || s.status === "failed").length;
    const pct = Math.round((done / total) * 100);
    return { done, total, pct };
  }, [build?.steps]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!build) return <p className="text-sm text-destructive">{t.ontologyBuild.notFound}</p>;
  const provider = build.extraction_provider ?? build.provider;
  const model = build.extraction_model ?? build.model;

  const progressLabel = t.ontologyBuild.stepsProgress
    .replace("{done}", String(stepsProgress.done))
    .replace("{total}", String(stepsProgress.total));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-mono text-lg">{build.id.slice(0, 8)}…</h1>
            <BuildStatusBadge status={build.status} />
            {build.domain && (
              <span className="rounded bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                {build.domain}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {t.ontologyBuild.documentLabel}{" "}
            <span className="font-mono">{build.document_id.slice(0, 8)}…</span> · Model{" "}
            {provider ?? t.ontologyUi.unknownProvider} / {model ?? t.ontologyUi.unknownModel} · Created{" "}
            <Time value={build.created_at} className="inline" /> · Updated <Time value={build.updated_at} className="inline" />
          </p>
          {build.error_message && (
            <p className="mt-2 text-sm text-destructive">{build.error_message}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link href="/ontology/builds">{t.ontologyBuild.back}</Link>
          </Button>
          {build.status === "failed" ? (
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => {
                const confirmed = window.confirm(
                  `Delete failed ontology build ${build.id.slice(0, 8)}?`,
                );
                if (!confirmed) return;
                deleteMutation.mutate();
              }}
            >
              {t.common.delete}
            </Button>
          ) : null}
          <PublishButton build={build} />
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">{t.ontologyBuild.statEntities}</p>
            <p className="text-2xl font-semibold">{build.entity_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">{t.ontologyBuild.statPendingEntities}</p>
            <p className="text-2xl font-semibold">{build.pending_entity_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">{t.ontologyBuild.statRelations}</p>
            <p className="text-2xl font-semibold">{build.relation_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">{t.ontologyBuild.statPendingRelations}</p>
            <p className="text-2xl font-semibold">{build.pending_relation_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs uppercase text-muted-foreground">{t.ontologyBuild.statExtractionModel}</p>
            <p className="text-sm font-semibold">{model ?? t.ontologyUi.unknownModel}</p>
            <p className="text-xs text-muted-foreground">{provider ?? t.ontologyUi.unknownProvider}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="entities">{t.ontologyBuild.tabEntities}</TabsTrigger>
          <TabsTrigger value="relations">{t.ontologyBuild.tabRelations}</TabsTrigger>
          <TabsTrigger value="steps">{t.ontologyBuild.tabSteps}</TabsTrigger>
        </TabsList>
        <TabsContent value="entities" className="space-y-3">
          {activeTab === "entities" && <CandidateEntitiesTable buildId={build.id} />}
        </TabsContent>
        <TabsContent value="relations" className="space-y-3">
          {activeTab === "relations" && <CandidateRelationsTable buildId={build.id} />}
        </TabsContent>
        <TabsContent value="steps" className="space-y-3">
          {build.steps.length > 0 && (
            <div className="space-y-2 rounded-lg border bg-muted/20 p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-foreground">{progressLabel}</span>
                <span className="tabular-nums text-muted-foreground">{stepsProgress.pct}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${stepsProgress.pct}%` }}
                />
              </div>
            </div>
          )}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t.ontologyBuild.stepColumnName}</TableHead>
                  <TableHead>{t.ontologyBuild.stepColumnStatus}</TableHead>
                  <TableHead>{t.ontologyBuild.stepColumnDetail}</TableHead>
                  <TableHead>{t.ontologyBuild.stepColumnStarted}</TableHead>
                  <TableHead>{t.ontologyBuild.stepColumnFinished}</TableHead>
                  <TableHead>{t.ontologyBuild.stepColumnDuration}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {build.steps.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-mono text-xs">{s.name}</TableCell>
                    <TableCell>
                      <StepStatusBadge status={s.status} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{s.detail ?? "—"}</TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      <Time value={s.started_at} className="inline" />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      <Time value={s.finished_at} className="inline" />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground tabular-nums">
                      {formatStepDuration(s.started_at, s.finished_at)}
                    </TableCell>
                  </TableRow>
                ))}
                {build.steps.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                      {t.ontologyBuild.noSteps}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
