"use client";

import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { PageHero } from "@/components/layout/page-hero";
import { PageShell } from "@/components/layout/page-shell";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function SettingsPage() {
  const { t } = useI18n();

  return (
    <PageShell maxWidth="6xl" className="flex flex-col gap-6 py-8">
      <PageHero title={t.settingsPage.title} description={t.settingsPage.description} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(340px,0.9fr)]">
        <Card variant="surface">
          <CardHeader>
            <CardTitle className="text-base">{t.settingsPage.languageTitle}</CardTitle>
            <CardDescription>{t.settingsPage.languageDescription}</CardDescription>
          </CardHeader>
          <CardContent>
            <LanguageSwitcher />
          </CardContent>
        </Card>
        <Card className="border-dashed">
          <CardHeader>
            <CardTitle className="text-base">{t.settingsPage.agentProfilesTitle}</CardTitle>
            <CardDescription>{t.settingsPage.agentProfilesDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>{t.settingsPage.agentProfilesDescription}</p>
            <Link
              href="/agents"
              className="inline-flex text-sm font-medium text-primary underline-offset-4 hover:underline"
            >
              {t.settingsPage.openAgents}
            </Link>
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
