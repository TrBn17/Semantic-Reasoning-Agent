"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, RefreshCcw, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { getSettings, updateSettings } from "@/shared/api/settings";
import type { SettingsResponse } from "@/shared/api/types";
import { SettingSection } from "@/components/settings/setting-row";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { cn } from "@/shared/utils";

type ProviderDraft = {
  enabled: boolean;
  values: Record<string, string>;
};

type SearchDefaultsDraft = {
  embedding_provider: string;
  embedding_model: string;
};

function hydrateProviderDrafts(settings: SettingsResponse): Record<string, ProviderDraft> {
  return Object.fromEntries(
    settings.providers.map((provider) => [
      provider.provider,
      {
        enabled: provider.enabled,
        values: Object.fromEntries(
          provider.fields.map((field) => {
            const value = provider.values.find((item) => item.key === field.key);
            const initialValue =
              value?.source === "database" && !field.secret ? value.display_value : "";
            return [field.key, initialValue];
          }),
        ),
      },
    ]),
  );
}

function draftsEqual(a: Record<string, ProviderDraft>, b: Record<string, ProviderDraft>): boolean {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const key of keys) {
    const left = a[key];
    const right = b[key];
    if (!left || !right) return false;
    if (left.enabled !== right.enabled) return false;
    const valueKeys = new Set([...Object.keys(left.values), ...Object.keys(right.values)]);
    for (const vk of valueKeys) {
      if ((left.values[vk] ?? "") !== (right.values[vk] ?? "")) return false;
    }
  }
  return true;
}

function searchDefaultsEqual(left: SearchDefaultsDraft, right: SearchDefaultsDraft): boolean {
  return (
    left.embedding_provider === right.embedding_provider &&
    left.embedding_model === right.embedding_model
  );
}

export function ProviderSettingsView() {
  const { t, language } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useActiveWorkspaceId();
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: queryKeys.settings.bootstrap(workspaceId),
    queryFn: () => getSettings(workspaceId),
  });
  const [providerDrafts, setProviderDrafts] = useState<Record<string, ProviderDraft>>({});
  const [searchDefaultsDraft, setSearchDefaultsDraft] = useState<SearchDefaultsDraft>({
    embedding_provider: "",
    embedding_model: "",
  });
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const hydratedDrafts = useMemo(() => (data ? hydrateProviderDrafts(data) : {}), [data]);
  const hasHydratedDrafts = useMemo(() => {
    if (!data) return false;
    return Object.keys(providerDrafts).length >= data.providers.length;
  }, [data, providerDrafts]);

  useEffect(() => {
    if (!data) return;
    setProviderDrafts(hydrateProviderDrafts(data));
    setSearchDefaultsDraft({
      embedding_provider: data.search_defaults.embedding_provider,
      embedding_model: data.search_defaults.embedding_model,
    });
  }, [data]);

  const baselineDrafts = hydratedDrafts;
  const baselineSearchDefaults = useMemo(
    () => ({
      embedding_provider: data?.search_defaults.embedding_provider ?? "",
      embedding_model: data?.search_defaults.embedding_model ?? "",
    }),
    [data?.search_defaults.embedding_model, data?.search_defaults.embedding_provider],
  );
  const isDirty = useMemo(
    () =>
      hasHydratedDrafts &&
      (!draftsEqual(providerDrafts, baselineDrafts) ||
        !searchDefaultsEqual(searchDefaultsDraft, baselineSearchDefaults)),
    [hasHydratedDrafts, providerDrafts, baselineDrafts, searchDefaultsDraft, baselineSearchDefaults],
  );

  const mutation = useMutation({
    mutationFn: () => {
      const resolvedWorkspaceId = data?.workspace.id ?? workspaceId;
      if (!resolvedWorkspaceId) {
        throw new Error("Workspace is not resolved.");
      }
      return updateSettings({
        workspace_id: resolvedWorkspaceId,
        providers:
          data?.providers.map((provider) => ({
            provider: provider.provider,
            enabled: providerDrafts[provider.provider]?.enabled ?? provider.enabled,
            values:
              providerDrafts[provider.provider]?.values ??
              hydratedDrafts[provider.provider]?.values ??
              {},
          })) ?? [],
        search_defaults: searchDefaultsDraft,
      });
    },
    onSuccess: async (updated) => {
      const resolvedWorkspaceId = updated.workspace.id || workspaceId;
      queryClient.setQueryData(queryKeys.settings.bootstrap(resolvedWorkspaceId), updated);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.models(resolvedWorkspaceId) }),
      ]);
      toast.success(t.agentsSettings.toasts.agentSettingsSaved);
    },
    onError: (error) =>
      toast.error(`${t.agentsSettings.toasts.saveFailedPrefix} ${(error as Error).message}`),
  });

  if (isLoading || !data) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full rounded-xl" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-24 w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SettingSection
        title={t.agentsSettings.providerEnv.title}
        action={
          <div className="flex items-center gap-2">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => void refetch()}
              disabled={isFetching || mutation.isPending}
              aria-label={t.common.refresh}
            >
              <RefreshCcw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || !hasHydratedDrafts || !isDirty}
            >
              <Save className="mr-1.5 h-3.5 w-3.5" />
              {language === "vi" ? "Luu" : t.common.save}
            </Button>
          </div>
        }
      >
        <div className="divide-y">
          <div className="space-y-3 py-3">
            <div className="text-sm font-medium">Workspace Search Embeddings</div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="search-embedding-provider" className="text-xs font-medium">
                  Embedding provider
                </Label>
                <Input
                  id="search-embedding-provider"
                  value={searchDefaultsDraft.embedding_provider}
                  onChange={(event) =>
                    setSearchDefaultsDraft((current) => ({
                      ...current,
                      embedding_provider: event.target.value,
                    }))
                  }
                  className="h-8 text-sm"
                  placeholder="cloudflare"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="search-embedding-model" className="text-xs font-medium">
                  Embedding model
                </Label>
                <Input
                  id="search-embedding-model"
                  value={searchDefaultsDraft.embedding_model}
                  onChange={(event) =>
                    setSearchDefaultsDraft((current) => ({
                      ...current,
                      embedding_model: event.target.value,
                    }))
                  }
                  className="h-8 text-sm"
                  placeholder="@cf/baai/bge-base-en-v1.5"
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">{data.search_defaults.reason}</p>
          </div>
          {data.providers.map((provider) => {
            const draft = providerDrafts[provider.provider];
            const isOpen = expanded[provider.provider] ?? false;
            const enabled = draft?.enabled ?? provider.enabled;
            const hasFields = provider.fields.length > 0;

            return (
              <div key={provider.provider} className="py-3">
                <div className="flex items-center justify-between gap-3">
                  <button
                    type="button"
                    className="group flex min-w-0 flex-1 items-center gap-2 text-left"
                    onClick={() =>
                      setExpanded((current) => ({
                        ...current,
                        [provider.provider]: !isOpen,
                      }))
                    }
                    aria-expanded={isOpen}
                    aria-controls={`provider-panel-${provider.provider}`}
                  >
                    {hasFields ? (
                      isOpen ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
                      )
                    ) : (
                      <span className="inline-block h-4 w-4 shrink-0" aria-hidden />
                    )}
                    <span className="truncate text-sm font-medium">{provider.label}</span>
                  </button>

                  <ToggleSwitch
                    checked={enabled}
                    onChange={(next) =>
                      setProviderDrafts((current) => ({
                        ...current,
                        [provider.provider]: {
                          enabled: next,
                          values:
                            current[provider.provider]?.values ??
                            hydrateProviderDrafts(data)[provider.provider].values,
                        },
                      }))
                    }
                    ariaLabel={`${t.agentsSettings.providerEnv.enabled} ${provider.label}`}
                  />
                </div>

                {isOpen && hasFields && (
                  <div
                    id={`provider-panel-${provider.provider}`}
                    className="mt-3 space-y-3 rounded-lg border bg-background/60 p-3"
                  >
                    {provider.fields.map((field) => {
                      const valueState = provider.values.find((value) => value.key === field.key);
                      const inputId = `${provider.provider}-${field.key}`;
                      return (
                        <div key={field.key} className="space-y-1.5">
                          <Label htmlFor={inputId} className="text-xs font-medium">
                            {field.label}
                          </Label>
                          <Input
                            id={inputId}
                            type={field.secret ? "password" : "text"}
                            placeholder={field.placeholder}
                            title={
                              [
                                field.help_text,
                                valueState?.configured && !draft?.values[field.key]
                                  ? `${t.agentsSettings.providerEnv.currentPrefix} ${
                                      valueState.display_value ||
                                      t.agentsSettings.providerEnv.configured
                                    }`
                                  : "",
                              ]
                                .filter(Boolean)
                                .join(" · ") || undefined
                            }
                            value={draft?.values[field.key] ?? ""}
                            onChange={(event) =>
                              setProviderDrafts((current) => ({
                                ...current,
                                [provider.provider]: {
                                  enabled: current[provider.provider]?.enabled ?? provider.enabled,
                                  values: {
                                    ...(current[provider.provider]?.values ??
                                      hydrateProviderDrafts(data)[provider.provider].values),
                                    [field.key]: event.target.value,
                                  },
                                },
                              }))
                            }
                            className="h-8 text-sm"
                          />
                        </div>
                      );
                    })}
                  </div>
                )}

                {isOpen && !hasFields && (
                  <p className="mt-2 pl-6 text-xs text-muted-foreground">
                    {t.agentsSettings.providerEnv.noAdditionalEnv}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </SettingSection>
    </div>
  );
}

function ToggleSwitch({
  checked,
  onChange,
  ariaLabel,
}: {
  checked: boolean;
  onChange: (next: boolean) => void;
  ariaLabel: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-5 w-9 shrink-0 items-center rounded-full border transition-colors",
        checked ? "bg-primary border-primary" : "bg-muted border-border",
      )}
    >
      <span
        className={cn(
          "inline-block h-4 w-4 transform rounded-full bg-background shadow transition-transform",
          checked ? "translate-x-4" : "translate-x-0.5",
        )}
      />
    </button>
  );
}
