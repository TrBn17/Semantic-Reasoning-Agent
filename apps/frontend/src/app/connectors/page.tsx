"use client";

import { PageShell } from "@/components/layout/page-shell";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function ConnectorsPage() {
  const { t } = useI18n();

  return (
    <PageShell>
      <h1 className="text-xl font-semibold tracking-tight">{t.placeholderPages.connectors.title}</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
        {t.placeholderPages.connectors.description}
      </p>
    </PageShell>
  );
}
