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
import type { OntologyBuildStepResponse } from "@/shared/api/types";
import type { Dictionary } from "@/shared/i18n/dictionaries";

const ONTOLOGY_STEP_PIPELINE_ORDER = [
  "classify_document_domain",
  "extract_entities",
  "extract_relations",
  "resolve_entities",
  "build_graph_upsert_plan",
  "sync_neo4j",
] as const;

function sortOntologySteps(steps: OntologyBuildStepResponse[]): OntologyBuildStepResponse[] {
  const rank = (name: string) => {
    const idx = ONTOLOGY_STEP_PIPELINE_ORDER.indexOf(name as (typeof ONTOLOGY_STEP_PIPELINE_ORDER)[number]);
    return idx === -1 ? ONTOLOGY_STEP_PIPELINE_ORDER.length : idx;
  };
  return [...steps].sort((a, b) => rank(a.name) - rank(b.name));
}

function metadataForJsonView(meta: Record<string, unknown>): Record<string, unknown> {
  try {
    const out = JSON.parse(JSON.stringify(meta)) as Record<string, unknown>;
    const trace = out.safe_trace;
    if (trace && typeof trace === "object" && trace !== null && !Array.isArray(trace)) {
      const tr = trace as Record<string, unknown>;
      if (Array.isArray(tr.chunks)) {
        tr.chunks = { omitted: true, count: tr.chunks.length };
      }
    }
    return out;
  } catch {
    return meta;
  }
}

function BuildStepPanel({
  step,
  labels,
}: {
  step: OntologyBuildStepResponse;
  labels: Dictionary["ontologyBuild"];
}) {
  const metadata = (step.metadata ?? {}) as Record<string, unknown>;
  const safeTrace =
    metadata.safe_trace && typeof metadata.safe_trace === "object" && !Array.isArray(metadata.safe_trace)
      ? (metadata.safe_trace as Record<string, unknown>)
      : null;
  const mergeStatsRoot =
    metadata.merge_stats && typeof metadata.merge_stats === "object" && !Array.isArray(metadata.merge_stats)
      ? (metadata.merge_stats as Record<string, unknown>)
      : null;
  const mergeStatsNested =
    safeTrace?.merge_stats && typeof safeTrace.merge_stats === "object" && !Array.isArray(safeTrace.merge_stats)
      ? (safeTrace.merge_stats as Record<string, unknown>)
      : null;
  const mergeStats = mergeStatsRoot ?? mergeStatsNested;
  const chunking =
    safeTrace?.chunking && typeof safeTrace.chunking === "object" && !Array.isArray(safeTrace.chunking)
      ? (safeTrace.chunking as Record<string, unknown>)
      : null;
  const traceErrors = Array.isArray(safeTrace?.errors) ? (safeTrace.errors as string[]) : [];
  const stepHelp =
    step.name === "extract_entities"
      ? labels.extractEntitiesStepHelp
      : step.name === "resolve_entities"
        ? labels.resolveEntitiesStepHelp
        : null;
  const promptVersion =
    typeof metadata.prompt_version === "string" ? metadata.prompt_version : null;

  const n = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);
  const hasMergeNumbers =
    mergeStats &&
    (n(mergeStats.raw_entity_rows_from_llm) !== null ||
      n(mergeStats.canonical_entities_after_merge) !== null ||
      n(mergeStats.raw_relation_rows_from_llm) !== null ||
      n(mergeStats.canonical_relations_after_merge) !== null);

  return (
    <div className="rounded-xl border bg-background p-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-mono text-sm font-medium">{step.name}</p>
            <StepStatusBadge status={step.status} />
          </div>
          {stepHelp ? (
            <p className="text-xs leading-relaxed text-muted-foreground">{stepHelp}</p>
          ) : null}
          <p className="text-sm text-foreground/90">{step.detail ?? "—"}</p>
          {promptVersion ? (
            <p className="text-xs text-muted-foreground">
              {labels.promptVersionLabel}: <span className="font-mono">{promptVersion}</span>
            </p>
          ) : null}
        </div>
        <div className="shrink-0 text-xs text-muted-foreground sm:text-right">
          <p>
            <Time value={step.started_at} className="inline" />
          </p>
          <p>{formatStepDuration(step.started_at, step.finished_at)}</p>
        </div>
      </div>

      {hasMergeNumbers ? (
        <div className="mt-3 rounded-lg border bg-muted/30 p-3">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {labels.mergeStatsHeading}
          </p>
          <dl className="grid gap-1.5 text-xs sm:grid-cols-2">
            {n(mergeStats!.raw_entity_rows_from_llm) !== null ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatRawEntityRows}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.raw_entity_rows_from_llm as number}</dd>
              </>
            ) : null}
            {n(mergeStats!.canonical_entities_after_merge) !== null ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatCanonicalEntities}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.canonical_entities_after_merge as number}</dd>
              </>
            ) : null}
            {n(mergeStats!.raw_relation_rows_from_llm) !== null ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatRawRelationRows}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.raw_relation_rows_from_llm as number}</dd>
              </>
            ) : null}
            {n(mergeStats!.canonical_relations_after_merge) !== null ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatCanonicalRelations}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.canonical_relations_after_merge as number}</dd>
              </>
            ) : null}
            {n(mergeStats!.entity_dedup_savings) !== null && (mergeStats!.entity_dedup_savings as number) > 0 ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatEntityDeduped}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.entity_dedup_savings as number}</dd>
              </>
            ) : null}
            {n(mergeStats!.relation_dedup_savings) !== null && (mergeStats!.relation_dedup_savings as number) > 0 ? (
              <>
                <dt className="text-muted-foreground">{labels.mergeStatRelationDeduped}</dt>
                <dd className="font-mono tabular-nums">{mergeStats!.relation_dedup_savings as number}</dd>
              </>
            ) : null}
          </dl>
          {typeof mergeStats!.resolution_rule === "string" && mergeStats!.resolution_rule.trim() ? (
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              <span className="font-medium text-foreground/80">{labels.mergeStatResolutionRule}: </span>
              {mergeStats!.resolution_rule as string}
            </p>
          ) : null}
        </div>
      ) : null}

      {chunking && (step.name === "extract_entities" || step.name === "extract_relations") ? (
        <div className="mt-3 rounded-lg border bg-muted/20 p-3">
          <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {labels.chunkingSummaryHeading}
          </p>
          <pre className="max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] text-muted-foreground">
            {JSON.stringify(chunking, null, 2)}
          </pre>
        </div>
      ) : null}

      {traceErrors.length > 0 ? (
        <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
          <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-amber-800 dark:text-amber-200">
            {labels.traceErrorsHeading}
          </p>
          <ul className="list-inside list-disc text-xs text-amber-900 dark:text-amber-100">
            {traceErrors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {Object.keys(metadata).length > 0 ? (
        <details className="mt-3 rounded-lg border bg-muted/10 p-2">
          <summary className="cursor-pointer text-xs font-medium text-muted-foreground">{labels.technicalMetadata}</summary>
          <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md bg-muted/40 p-2 font-mono text-[10px] leading-relaxed">
            {JSON.stringify(metadataForJsonView(metadata), null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}

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

  const orderedSteps = useMemo(
    () => (build?.steps.length ? sortOntologySteps(build.steps) : []),
    [build?.steps],
  );

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!build) return <p className="text-sm text-destructive">{t.ontologyBuild.notFound}</p>;

  const provider = build.extraction_provider ?? build.provider;
  const model = build.extraction_model ?? build.model;
  const pendingReview = build.pending_entity_count + build.pending_relation_count;
  const title = build.ontology_title || t.ontologyBuild.tableBuild;
  const hasPublishableEntities = build.has_publishable_entities ?? build.entity_count > 0;
  const canPublishByStatus = build.status === "completed" || build.status === "published";
  const canPublish = canPublishByStatus && hasPublishableEntities;
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
          {!hasPublishableEntities && canPublishByStatus ? (
            <p className="text-sm text-amber-600">{t.ontologyBuild.publishUnavailableNoEntities}</p>
          ) : null}
          {build.error_message ? <p className="text-sm text-destructive">{build.error_message}</p> : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            disabled={publishMutation.isPending || !canPublish}
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
          {orderedSteps.length > 0 ? (
            <details className="rounded-xl border bg-muted/20 p-3" open>
              <summary className="cursor-pointer text-sm font-medium">{t.ontologyBuild.tabSteps}</summary>
              <div className="mt-3 space-y-3">
                {orderedSteps.map((step) => (
                  <BuildStepPanel key={step.id} step={step} labels={t.ontologyBuild} />
                ))}
              </div>
            </details>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
