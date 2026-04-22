"use client";

import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SettingRow, SettingSection } from "@/components/settings/setting-row";
import { getSettings } from "@/shared/api/settings";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { cn } from "@/shared/utils";

export function GeneralSettingsPanel() {
  const { t, language, setLanguage } = useI18n();
  const workspaceId = useActiveWorkspaceId();
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.settings.bootstrap(workspaceId),
    queryFn: () => getSettings(workspaceId),
  });

  const providerCount = data?.providers.filter((provider) => provider.ready).length ?? 0;
  const totalProviders = data?.providers.length ?? 0;

  if (isLoading || !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-36 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SettingSection
        title={t.generalSettings.workspace.title}
        description={t.generalSettings.workspace.description}
      >
        <SettingRow
          label={t.generalSettings.workspace.nameLabel}
          description={data.workspace.id}
          control={<span className="text-sm font-medium">{data.workspace.name}</span>}
        />
        <SettingRow
          label={t.generalSettings.workspace.readyProvidersLabel}
          description={t.generalSettings.workspace.readyProvidersDescription}
          control={
            <Badge variant={providerCount > 0 ? "success" : "warning"}>
              {providerCount} / {totalProviders}
            </Badge>
          }
        />
      </SettingSection>

      <SettingSection
        title={t.generalSettings.appearance.title}
        description={t.generalSettings.appearance.description}
      >
        <SettingRow
          label={t.generalSettings.appearance.languageLabel}
          description={t.generalSettings.appearance.languageDescription}
          control={
            <div className="inline-flex rounded-md border bg-muted/40 p-0.5">
              <Button
                type="button"
                size="sm"
                variant={language === "en" ? "default" : "ghost"}
                className="h-7 rounded-sm px-3 text-xs"
                onClick={() => setLanguage("en")}
              >
                {t.languageOptions.english}
              </Button>
              <Button
                type="button"
                size="sm"
                variant={language === "vi" ? "default" : "ghost"}
                className="h-7 rounded-sm px-3 text-xs"
                onClick={() => setLanguage("vi")}
              >
                {t.languageOptions.vietnamese}
              </Button>
            </div>
          }
        />
        <ThemeRow />
      </SettingSection>
    </div>
  );
}

function ThemeRow() {
  const { t } = useI18n();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const current = theme ?? "system";
  const effective = mounted ? (resolvedTheme ?? current) : current;

  const options = [
    {
      id: "light",
      label: t.generalSettings.appearance.themeOptions.light,
      icon: Sun,
    },
    {
      id: "dark",
      label: t.generalSettings.appearance.themeOptions.dark,
      icon: Moon,
    },
    {
      id: "system",
      label: t.generalSettings.appearance.themeOptions.system,
      icon: Monitor,
    },
  ] as const;

  return (
    <SettingRow
      label={t.generalSettings.appearance.themeLabel}
      description={
        mounted
          ? `${t.generalSettings.appearance.themeAppliedPrefix} ${effective}`
          : t.generalSettings.appearance.themeLoading
      }
      control={
        <div className="inline-flex rounded-md border bg-muted/40 p-0.5">
          {options.map((option) => {
            const Icon = option.icon;
            const selected = current === option.id;
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => setTheme(option.id)}
                aria-pressed={selected}
                className={cn(
                  "inline-flex h-7 items-center gap-1.5 rounded-sm px-2.5 text-xs transition-colors",
                  selected
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className="h-3.5 w-3.5" aria-hidden />
                {option.label}
              </button>
            );
          })}
        </div>
      }
    />
  );
}
