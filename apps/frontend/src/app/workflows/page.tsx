"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useI18n } from "@/shared/i18n/use-language";

export default function WorkflowsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">{t.pages.workflows.title}</h1>
      </div>
      <Card>
        <CardContent className="flex items-center justify-between gap-3 p-4">
          <Badge variant="secondary">{t.pages.workflows.comingSoonBadge}</Badge>
        </CardContent>
      </Card>
    </div>
  );
}
