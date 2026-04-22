"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useSettingsModelsQuery } from "@/shared/hooks/use-settings-models-query";
import { useI18n } from "@/shared/i18n/use-language";
import { rankItems } from "@/shared/utils/fuzzy";
import { SettingSection } from "@/components/settings/setting-row";

export function SettingsModelsView() {
  const { t, language } = useI18n();
  const { data = [], isLoading } = useSettingsModelsQuery();

  const [query, setQuery] = useState("");
  const [providerFilter, setProviderFilter] = useState<string>("all");
  const [onlyReady, setOnlyReady] = useState(false);

  const providers = useMemo(() => {
    const set = new Set<string>();
    data.forEach((model) => set.add(model.provider));
    return Array.from(set).sort();
  }, [data]);

  const filtered = useMemo(() => {
    const scoped = data.filter((model) => {
      if (providerFilter !== "all" && model.provider !== providerFilter) return false;
      if (onlyReady && !model.ready) return false;
      return true;
    });

    const ranked = query.trim()
      ? rankItems(scoped, query, (model) => [
          model.label,
          model.model,
          model.provider,
          model.reason,
          model.context_window ? `${Math.round(model.context_window / 1000)}k` : "",
        ]).map(({ item }) => item)
      : scoped;

    return [...ranked].sort((a, b) => {
      if (a.ready !== b.ready) return a.ready ? -1 : 1;
      return a.label.localeCompare(b.label);
    });
  }, [data, onlyReady, providerFilter, query]);

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-10 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-xl" />
        <Skeleton className="h-10 w-full rounded-xl" />
      </div>
    );
  }

  const readyCount = filtered.filter((model) => model.ready).length;

  return (
    <div className="space-y-6">
      <SettingSection
        title={language === "vi" ? "Bộ lọc" : "Filters"}
        action={
          <Badge variant="outline" className="text-[10px]">
            {readyCount} / {filtered.length} {language === "vi" ? "sẵn sàng" : "ready"}
          </Badge>
        }
      >
        <div className="grid gap-3 py-2 sm:grid-cols-[1fr_auto_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t.common.search}
              className="h-8 pl-8 text-sm"
              aria-label={t.common.search}
            />
          </div>
          <select
            value={providerFilter}
            onChange={(event) => setProviderFilter(event.target.value)}
            className="h-8 rounded-md border bg-background px-2 text-sm"
            aria-label={language === "vi" ? "Nhà cung cấp" : "Provider"}
          >
            <option value="all">{t.agentsSettings.picker.allProviders}</option>
            {providers.map((provider) => (
              <option key={provider} value={provider}>
                {provider}
              </option>
            ))}
          </select>
          <label className="inline-flex h-8 items-center gap-2 rounded-md border px-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={onlyReady}
              onChange={(event) => setOnlyReady(event.target.checked)}
              className="h-3.5 w-3.5"
            />
            {t.agentsSettings.picker.onlyReady}
          </label>
        </div>
      </SettingSection>

      <SettingSection
        title={language === "vi" ? "Danh mục model" : "Model catalog"}
        description={
          language === "vi"
            ? "Mô hình hiển thị đúng với thứ tự backend trả về."
            : "Models exposed by the backend settings endpoint, in backend order."
        }
      >
        {filtered.length === 0 ? (
          <div className="py-10 text-center text-sm text-muted-foreground">
            {t.common.noMatches}
          </div>
        ) : (
          <ul className="divide-y" role="list">
            {filtered.map((model) => (
              <li
                key={`${model.provider}:${model.model}`}
                className="flex items-center gap-3 py-2.5 text-sm"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="truncate font-medium">{model.label}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {model.provider}
                    </Badge>
                    {model.context_window ? (
                      <Badge variant="outline" className="text-[10px]">
                        {model.context_window} ctx
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    <span className="font-mono">{model.model}</span>
                    {model.reason ? ` · ${model.reason}` : ""}
                  </p>
                </div>
                <Badge
                  variant={model.ready ? "success" : "warning"}
                  className="shrink-0 text-[10px]"
                >
                  {model.ready
                    ? language === "vi"
                      ? "sẵn sàng"
                      : "ready"
                    : language === "vi"
                    ? "chặn"
                    : "blocked"}
                </Badge>
              </li>
            ))}
          </ul>
        )}
      </SettingSection>
    </div>
  );
}
