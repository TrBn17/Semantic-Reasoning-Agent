"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { BuildStatusBadge, StepStatusBadge } from "@/components/ontology/status-badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteBuild, getBuild, publishGraphDraft } from "@/shared/api/ontology";
import { Time } from "@/shared/components/time";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { notify } from "@/shared/ui/notify";
import { formatStepDuration } from "@/shared/utils";

function SummaryCard({
  label,
  value,
  hint,
  valueClassName,
}: {
  label: string;
  value: string | number;
  hint?: string;
  valueClassName?: string;
}) {
  return (
    <Card className="rounded-2xl border">
      <CardContent className="space-y-1 p-4">
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className={`break-words text-2xl font-semibold ${valueClassName ?? ""}`}>{value}</p>
        {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}

export function BuildDetail({ buildId }: { buildId: string }) {
  const { t } = useI18n();
  const queryClient = useQueryClient();

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
      notify.success(t.ontologyBuild.deleted);
      window.location.href = "/ontology/builds";
    },
    onError: (err) => {
      notify.error(err, t.ontologyBuild.deleteFailed);
    },
  });

  const publishMutation = useMutation({
    mutationFn: () =>
      publishGraphDraft({
        workspace_id: build?.workspace_id,
        build_id: build?.id,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      notify.success(t.ontologyBuild.publishSuccess);
    },
    onError: (err) => {
      notify.error(err, t.ontologyBuild.publishFailed);
    },
  });

  const stepsProgress = useMemo(() => {
    if (!build?.steps.length) return { done: 0, total: 0, pct: 0 };
    const total = build.steps.length;
    const done = build.steps.filter((step) => step.status === "completed" || step.status === "failed").length;
    return { done, total, pct: Math.round((done / total) * 100) };
  }, [build?.steps]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!build) return <p className="text-sm text-destructive">{t.ontologyBuild.notFound}</p>;

  const provider = build.extraction_provider ?? build.provider;
  const model = build.extraction_model ?? build.model;
  const pendingReview = build.pending_entity_count + build.pending_relation_count;
  const title = build.ontology_title || t.ontologyBuild.tableBuild;
  const progressLabel = t.ontologyBuild.stepsProgress
    .replace("{done}", String(stepsProgress.done))
    .replace("{total}", String(stepsProgress.total));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-3xl border bg-card p-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <BuildStatusBadge status={build.status} />
            {build.domain ? (
              <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                {build.domain}
              </span>
            ) : null}
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span>
              {t.ontologyBuild.tableUpdated} <Time value={build.updated_at} className="inline" />
            </span>
          </div>
          {build.error_message ? <p className="text-sm text-destructive">{build.error_message}</p> : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            disabled={publishMutation.isPending || (build.status !== "completed" && build.status !== "published")}
            onClick={() => publishMutation.mutate()}
          >
            {publishMutation.isPending ? t.ontologyBuild.publishing : t.ontologyBuild.publish}
          </Button>
          <Button asChild variant="outline">
            <Link href="/ontology/builds">{t.ontologyBuild.back}</Link>
          </Button>
          {build.status === "failed" ? (
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => {
                const confirmed = window.confirm(`Delete failed ontology build ${build.id.slice(0, 8)}?`);
                if (!confirmed) return;
                deleteMutation.mutate();
              }}
            >
              {t.common.delete}
            </Button>
          ) : null}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label={t.ontologyBuild.tablePending} value={pendingReview} />
        <SummaryCard label={t.ontologyBuild.tabEntities} value={build.entity_count} />
        <SummaryCard label={t.ontologyBuild.tabRelations} value={build.relation_count} />
        <SummaryCard
          label={t.ontologyBuild.statExtractionModel}
          value={model ?? t.ontologyUi.unknownModel}
          hint={provider ?? t.ontologyUi.unknownProvider}
          valueClassName="text-xl leading-tight break-all sm:text-2xl"
        />
      </div>

      <Card className="rounded-2xl border">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{progressLabel}</p>
              <p className="text-xs text-muted-foreground">{t.ontologyBuild.tablePending}: {pendingReview}</p>
            </div>
            <span className="text-sm font-semibold tabular-nums">{stepsProgress.pct}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${stepsProgress.pct}%` }}
            />
          </div>
          {build.steps.length > 0 ? (
            <details className="rounded-xl border bg-muted/20 p-3">
              <summary className="cursor-pointer text-sm font-medium">{t.ontologyBuild.tabSteps}</summary>
              <div className="mt-3 space-y-3">
                {build.steps.map((step) => {
                  return (
                    <div key={step.id} className="rounded-xl bg-background p-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium">{step.name}</p>
                            <StepStatusBadge status={step.status} />
                          </div>
                          <p className="text-sm text-muted-foreground">{step.detail ?? "-"}</p>
                        </div>
                        <div className="text-xs text-muted-foreground sm:text-right">
                          <p>
                            <Time value={step.started_at} className="inline" />
                          </p>
                          <p>{formatStepDuration(step.started_at, step.finished_at)}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </details>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
