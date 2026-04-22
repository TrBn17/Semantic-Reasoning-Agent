"use client";

import { useI18n } from "@/shared/i18n/use-language";

export default function ArtifactsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-4xl space-y-4 p-6">
      <h1 className="text-2xl font-semibold">{t.pages.artifacts.title}</h1>
      <div className="rounded-md border border-dashed bg-muted/20 p-8 text-sm text-muted-foreground">
        {t.pages.artifacts.description}
      </div>
    </div>
  );
}
