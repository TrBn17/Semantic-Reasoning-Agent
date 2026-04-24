"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { Cog, Key, Layers, type LucideIcon } from "lucide-react";
import { GeneralSettingsPanel } from "@/components/settings/general-settings-panel";
import { ProviderSettingsView } from "@/components/settings/provider-settings-view";
import { SettingsModelsView } from "@/components/settings/settings-models-view";
import { useI18n } from "@/shared/i18n/use-language";
import { cn } from "@/shared/utils";

type TabId = "general" | "providers" | "models";

type TabDef = {
  id: TabId;
  label: string;
  icon: LucideIcon;
};

const DEFAULT_TAB: TabId = "general";
const VALID_TABS: readonly TabId[] = ["general", "providers", "models"] as const;

function isValidTab(value: string | null): value is TabId {
  return value !== null && (VALID_TABS as readonly string[]).includes(value);
}

export function SettingsShell({ defaultTab = DEFAULT_TAB }: { defaultTab?: TabId } = {}) {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();

  const activeTab = useMemo<TabId>(() => {
    const raw = searchParams.get("tab");
    return isValidTab(raw) ? raw : defaultTab;
  }, [defaultTab, searchParams]);

  const setTab = useCallback(
    (next: TabId) => {
      const params = new URLSearchParams(searchParams.toString());
      if (next === DEFAULT_TAB) {
        params.delete("tab");
      } else {
        params.set("tab", next);
      }
      const query = params.toString();
      router.replace(query ? `/settings?${query}` : "/settings", { scroll: false });
    },
    [router, searchParams],
  );

  const tabs: TabDef[] = useMemo(
    () => [
      {
        id: "general",
        label: t.settingsShell.general.label,
        icon: Cog,
      },
      {
        id: "providers",
        label: t.settingsShell.providers.label,
        icon: Key,
      },
      {
        id: "models",
        label: t.settingsShell.models.label,
        icon: Layers,
      },
    ],
    [t],
  );

  const activeMeta = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl gap-6 px-4 py-6 md:gap-8 md:px-6">
      <aside className="hidden w-56 shrink-0 border-r pr-4 md:block">
        <div className="sticky top-6 space-y-1">
          <div className="mb-3 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {t.nav.settings}
          </div>
          <nav aria-label={t.common.accessibility.settingsSections} className="space-y-0.5">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const selected = tab.id === activeTab;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setTab(tab.id)}
                  aria-current={selected ? "page" : undefined}
                  className={cn(
                    "group flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors",
                    selected
                      ? "bg-muted text-foreground"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" aria-hidden />
                  <span className="truncate">{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <div className="mb-6 md:hidden">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {t.nav.settings}
          </label>
          <select
            value={activeTab}
            onChange={(event) => setTab(event.target.value as TabId)}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
          >
            {tabs.map((tab) => (
              <option key={tab.id} value={tab.id}>
                {tab.label}
              </option>
            ))}
          </select>
        </div>

        <header className="mb-6">
          <h1 className="text-xl font-semibold tracking-tight">{activeMeta.label}</h1>
        </header>

        <section className="space-y-8 pb-16">
          {activeTab === "general" && <GeneralSettingsPanel />}
          {activeTab === "providers" && <ProviderSettingsView />}
          {activeTab === "models" && <SettingsModelsView />}
        </section>
      </div>
    </div>
  );
}
