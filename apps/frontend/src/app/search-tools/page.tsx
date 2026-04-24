"use client";

import { SearchToolsView } from "@/components/search-tools/search-tools-view";
import { useI18n } from "@/shared/i18n/use-language";
import { useEffect } from "react";

export default function SearchToolsPage() {
  const { t } = useI18n();
  useEffect(() => {
    // #region agent log
    fetch("http://127.0.0.1:7630/ingest/5124439d-c722-43d8-a824-62b24c1412e1", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "5bfbef" },
      body: JSON.stringify({
        sessionId: "5bfbef",
        runId: "baseline",
        hypothesisId: "H4",
        location: "search-tools/page.tsx:SearchToolsPage",
        message: "Search tools page header snapshot",
        data: {
          title: t.searchToolsPage.title,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
  }, [t]);
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.searchToolsPage.title}</h1>
      </div>
      <SearchToolsView />
    </div>
  );
}
