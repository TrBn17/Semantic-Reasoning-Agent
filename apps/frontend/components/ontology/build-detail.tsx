"use client";

import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Button } from "@/components/ui/button";
import { GraphStats } from "@/components/ontology/graph-stats";
import { useI18n } from "@/src/shared/i18n/use-language";

export function BuildDetail({ buildId }: { buildId: string }) {
  const { t } = useI18n();
  const d = t.knowledgeGraph.buildDetail;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-xl font-semibold">{d.title}</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            {d.description}{" "}
            <span className="font-mono">{buildId.slice(0, 12)}…</span>
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/ontology/builds">{d.back}</Link>
        </Button>
      </div>
      <GraphStats />
    </div>
  );
}
