"use client";

import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { PageHero } from "@/components/layout/page-hero";
import { PageShell } from "@/components/layout/page-shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function SettingsPage() {
  const { t } = useI18n();

  return (
    <PageShell maxWidth="6xl" className="flex flex-col gap-6 py-8">
      <PageHero title={t.settingsPage.title} description={t.settingsPage.description} />
      <Card variant="surface">
        <CardHeader>
          <CardTitle className="text-base">{t.settingsPage.languageTitle}</CardTitle>
          <CardDescription>{t.settingsPage.languageDescription}</CardDescription>
        </CardHeader>
        <CardContent>
          <LanguageSwitcher />
        </CardContent>
      </Card>
    </PageShell>
  );
}
