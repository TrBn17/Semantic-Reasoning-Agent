"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

import { ToolsTable } from "@/components/tools/tools-table";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/shared/i18n/use-language";

export default function ToolsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{t.pages.tools.title}</h1>
          <p className="text-sm text-muted-foreground">{t.pages.tools.description}</p>
        </div>
        <Button asChild variant="secondary" size="sm">
          <Link href="/search-tools">
            <Sparkles className="mr-1 h-4 w-4" /> Search tool builder
          </Link>
        </Button>
      </div>
      <ToolsTable />
    </div>
  );
}
