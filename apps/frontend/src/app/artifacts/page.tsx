"use client";

import { useI18n } from "@/shared/i18n/use-language";

export default function ArtifactsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-semibold">{t.pages.artifacts.title}</h1>
    </div>
  );
}
