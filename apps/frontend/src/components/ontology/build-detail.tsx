"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { toast } from "sonner";
import { BuildStatusBadge, StepStatusBadge } from "@/components/ontology/status-badges";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { deleteBuild, getBuild } from "@/shared/api/ontology";
import { Time } from "@/shared/components/time";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { formatStepDuration } from "@/shared/utils";

function renderSafeTrace(stepMetadata: Record<string, unknown> | undefined): string | null {
  if (!stepMetadata) return null;
  const trace = (stepMetadata.safe_trace ?? stepMetadata) as Record<string, unknown>;
  const provider = typeof trace.provider === "string" ? trace.provider : null;
  const model = typeof trace.model === "string" ? trace.model : null;
  const promptVersion = typeof trace.prompt_version === "string" ? trace.prompt_version : null;
  const finishReason = typeof trace.finish_reason === "string" ? trace.finish_reason : null;
  const domain = typeof trace.domain === "string" ? trace.domain : null;
  const usage = trace.usage as Record<string, unknown> | undefined;
  const inputTokens =
    usage && typeof usage.input_tokens === "number" ? usage.input_tokens : null;
  const outputTokens =
    usage && typeof usage.output_tokens === "number" ? usage.output_tokens : null;
  const entityCount = typeof trace.entity_count === "number" ? trace.entity_count : null;
  const relationCount = typeof trace.relation_count === "number" ? trace.relation_count : null;
  const chunkCount = typeof trace.chunk_count === "number" ? trace.chunk_count : null;
  const errors = Array.isArray(trace.errors)
    ? trace.errors.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
  const outputPreview =
    typeof trace.output_preview === "string" && trace.output_preview.trim()
      ? trace.output_preview.trim()
      : null;
  const summary = [
    provider && model ? `${provider}/${model}` : null,
    promptVersion ? `prompt ${promptVersion}` : null,
    finishReason ? `finish ${finishReason}` : null,
    domain ? `domain ${domain}` : null,
    inputTokens !== null || outputTokens !== null
      ? `tokens ${inputTokens ?? "?"}/${outputTokens ?? "?"}`
      : null,
    entityCount !== null ? `entities ${entityCount}` : null,
    relationCount !== null ? `relations ${relationCount}` : null,
    chunkCount !== null ? `chunks ${chunkCount}` : null,
  ]
    .filter(Boolean)
    .join(" · ");
  const firstError = errors.length > 0 ? `parse failed · ${errors[0]}` : null;
  const lines = [summary || null, firstError, outputPreview].filter(Boolean);
  if (lines.length === 0) return null;
  return lines.join("\n");
}

function SummaryCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <Card className="rounded-2xl border">
      <CardContent className="space-y-1 p-4">
        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
        <p className="text-2xl font-semibold">{value}</p>
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
    const done = build.steps.filter((step) => step.status === "completed" || step.status === "failed").length;
    return { done, total, pct: Math.round((done / total) * 100) };
  }, [build?.steps]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!build) return <p className="text-sm text-destructive">{t.ontologyBuild.notFound}</p>;

  const provider = build.extraction_provider ?? build.provider;
  const model = build.extraction_model ?? build.model;
  const pendingReview = build.pending_entity_count + build.pending_relation_count;
  const reviewedCount = build.entity_count + build.relation_count - pendingReview;
  const title = build.ontology_title || `${t.ontologyBuild.documentLabel} ${build.document_id.slice(0, 8)}...`;
  const progressLabel = t.ontologyBuild.stepsProgress
    .replace("{done}", String(stepsProgress.done))
    .replace("{total}", String(stepsProgress.total));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 rounded-3xl border bg-card p-5 md:flex-row md:items-start md:justify-between">
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
            <p className="text-sm text-muted-foreground">
              #{build.id.slice(0, 8)}... - {provider ?? t.ontologyUi.unknownProvider} /{" "}
              {model ?? t.ontologyUi.unknownModel}
            </p>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
            <span>
              {t.ontologyBuild.documentLabel} <span className="font-mono">{build.document_id.slice(0, 8)}...</span>
            </span>
            <span>
              Created <Time value={build.created_at} className="inline" />
            </span>
            <span>
              Updated <Time value={build.updated_at} className="inline" />
            </span>
          </div>
          {build.error_message ? <p className="text-sm text-destructive">{build.error_message}</p> : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
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

      <div className="grid gap-3 md:grid-cols-4">
        <SummaryCard label={t.ontologyBuild.tablePending} value={pendingReview} />
        <SummaryCard label={t.ontologyBuild.tabEntities} value={build.entity_count} />
        <SummaryCard label={t.ontologyBuild.tabRelations} value={build.relation_count} />
        <SummaryCard
          label={t.ontologyBuild.statExtractionModel}
          value={model ?? t.ontologyUi.unknownModel}
          hint={provider ?? t.ontologyUi.unknownProvider}
        />
      </div>

      <Card className="rounded-2xl border">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">{progressLabel}</p>
              <p className="text-xs text-muted-foreground">
                {reviewedCount} reviewed - {pendingReview} waiting
              </p>
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
              <summary className="cursor-pointer text-sm font-medium">Processing details</summary>
              <div className="mt-3 space-y-3">
                {build.steps.map((step) => {
                  const safeTrace = renderSafeTrace(step.metadata);
                  return (
                    <div key={step.id} className="rounded-xl bg-background p-3">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium">{step.name}</p>
                            <StepStatusBadge status={step.status} />
                          </div>
                          <p className="text-sm text-muted-foreground">{step.detail ?? "No extra detail."}</p>
                          {safeTrace ? (
                            <p className="whitespace-pre-wrap text-xs text-muted-foreground">{safeTrace}</p>
                          ) : null}
                        </div>
                        <div className="text-xs text-muted-foreground md:text-right">
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

      <Card className="rounded-2xl border">
        <CardContent className="p-4 text-sm text-muted-foreground">
          Candidate entity/relation persistence for ontology builds has been removed. Use the graph
          draft flow to curate and publish ontology changes.
        </CardContent>
      </Card>
    </div>
  );
}
