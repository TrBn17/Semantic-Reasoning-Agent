"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw, Save } from "lucide-react";
import { toast } from "sonner";
import { TaskModelPicker, composeModelValue, parseModelValue } from "@/components/agents/model-picker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { getSettings, updateSettings } from "@/lib/api/settings";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import type { SettingsResponse, SettingsProviderResponse } from "@/lib/api/types";

type ProviderDraft = {
  enabled: boolean;
  values: Record<string, string>;
};

function hydrateProviderDrafts(settings: SettingsResponse): Record<string, ProviderDraft> {
  return Object.fromEntries(
    settings.providers.map((provider) => [
      provider.provider,
      {
        enabled: provider.enabled,
        values: Object.fromEntries(
          provider.values.map((value) => [
            value.key,
            value.source === "database" ? value.display_value : "",
          ]),
        ),
      },
    ]),
  );
}

function hydrateTaskDrafts(settings: SettingsResponse): Record<string, string> {
  return Object.fromEntries(
    settings.task_defaults.map((task) => [task.task_type, composeModelValue(task.provider, task.model)]),
  );
}

function providerStatus(provider: SettingsProviderResponse, draft?: ProviderDraft) {
  const enabled = draft?.enabled ?? provider.enabled;
  if (!enabled) {
    return { label: "Disabled", variant: "secondary" as const };
  }
  return provider.ready
    ? { label: "Ready", variant: "success" as const }
    : { label: "Needs setup", variant: "warning" as const };
}

export function ProviderSettingsView() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: queryKeys.settings.bootstrap(workspaceId),
    queryFn: () => getSettings(workspaceId),
  });
  const [providerDrafts, setProviderDrafts] = useState<Record<string, ProviderDraft>>({});
  const [taskDrafts, setTaskDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!data) return;
    setProviderDrafts(hydrateProviderDrafts(data));
    setTaskDrafts(hydrateTaskDrafts(data));
  }, [data]);

  const mutation = useMutation({
    mutationFn: () =>
      updateSettings({
        workspace_id: data?.workspace.id ?? workspaceId ?? "workspace-demo",
        providers:
          data?.providers.map((provider) => ({
            provider: provider.provider,
            enabled: providerDrafts[provider.provider]?.enabled ?? provider.enabled,
            values: providerDrafts[provider.provider]?.values ?? {},
          })) ?? [],
        task_defaults:
          data?.task_defaults
            .map((task) => {
              const parsed = parseModelValue(taskDrafts[task.task_type]);
              if (!parsed) return null;
              return {
                use_case: task.use_case,
                provider: parsed.provider,
                model: parsed.model,
              };
            })
            .filter((item): item is NonNullable<typeof item> => Boolean(item)) ?? [],
      }),
    onSuccess: async (updated) => {
      queryClient.setQueryData(queryKeys.settings.bootstrap(workspaceId), updated);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.all }),
        queryClient.invalidateQueries({ queryKey: queryKeys.settings.models(workspaceId) }),
      ]);
      toast.success("Settings saved.");
    },
    onError: (error) => toast.error(`Save failed: ${(error as Error).message}`),
  });

  const providerCount = data?.providers.filter((provider) => provider.ready).length ?? 0;
  const modelCount = data?.model_catalog.filter((model) => model.ready).length ?? 0;

  const providerGroups = useMemo(
    () => Object.fromEntries((data?.model_catalog ?? []).map((model) => [composeModelValue(model.provider, model.model), model])),
    [data?.model_catalog],
  );

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-24">
      <Card>
        <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <CardTitle>Provider Configuration</CardTitle>
            <CardDescription>
              Configure provider credentials, inspect readiness, and choose workspace-level model defaults.
            </CardDescription>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm lg:flex">
            <div className="rounded-xl border px-4 py-3">
              <div className="text-muted-foreground">Workspace</div>
              <div className="font-semibold">{data.workspace.name}</div>
            </div>
            <div className="rounded-xl border px-4 py-3">
              <div className="text-muted-foreground">Ready providers</div>
              <div className="font-semibold">{providerCount}</div>
            </div>
            <div className="rounded-xl border px-4 py-3">
              <div className="text-muted-foreground">Ready models</div>
              <div className="font-semibold">{modelCount}</div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Providers</CardTitle>
            <CardDescription>Store keys or URLs here. Agent profiles no longer live on this page.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.providers.map((provider) => {
              const draft = providerDrafts[provider.provider];
              const status = providerStatus(provider, draft);
              return (
                <div key={provider.provider} className="rounded-2xl border p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{provider.label}</h3>
                        <Badge variant={status.variant}>{status.label}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{provider.status_text}</p>
                    </div>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={draft?.enabled ?? provider.enabled}
                        onChange={(event) =>
                          setProviderDrafts((current) => ({
                            ...current,
                            [provider.provider]: {
                              enabled: event.target.checked,
                              values: current[provider.provider]?.values ?? hydrateProviderDrafts(data)[provider.provider].values,
                            },
                          }))
                        }
                      />
                      Enabled
                    </label>
                  </div>

                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    {provider.fields.length === 0 && (
                      <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                        This provider does not require extra configuration.
                      </div>
                    )}
                    {provider.fields.map((field) => {
                      const valueState = provider.values.find((value) => value.key === field.key);
                      return (
                        <div key={field.key} className="space-y-2">
                          <Label htmlFor={`${provider.provider}-${field.key}`}>{field.label}</Label>
                          <Input
                            id={`${provider.provider}-${field.key}`}
                            type={field.secret ? "password" : "text"}
                            placeholder={field.placeholder}
                            value={draft?.values[field.key] ?? ""}
                            onChange={(event) =>
                              setProviderDrafts((current) => ({
                                ...current,
                                [provider.provider]: {
                                  enabled: current[provider.provider]?.enabled ?? provider.enabled,
                                  values: {
                                    ...(current[provider.provider]?.values ?? hydrateProviderDrafts(data)[provider.provider].values),
                                    [field.key]: event.target.value,
                                  },
                                },
                              }))
                            }
                          />
                          <p className="text-xs text-muted-foreground">
                            {field.help_text}
                            {valueState?.configured && !draft?.values[field.key]
                              ? ` Saved: ${valueState.display_value || "configured"}`
                              : ""}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Workspace Defaults</CardTitle>
              <CardDescription>These defaults apply before an agent profile overrides them.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.task_defaults.map((task) => {
                const selectedValue = taskDrafts[task.task_type];
                const selectedModel = selectedValue ? providerGroups[selectedValue] : null;
                return (
                  <div key={task.task_type} className="rounded-2xl border p-4">
                    <div className="mb-3">
                      <h3 className="font-semibold">{task.label}</h3>
                      <p className="text-sm text-muted-foreground">{task.description}</p>
                    </div>
                    <TaskModelPicker
                      models={data.model_catalog}
                      value={selectedValue}
                      onChange={(value) =>
                        setTaskDrafts((current) => ({ ...current, [task.task_type]: value }))
                      }
                    />
                    {selectedModel && (
                      <p className="mt-3 text-xs text-muted-foreground">
                        {selectedModel.ready ? "Ready" : "Blocked"}: {selectedModel.reason}
                      </p>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Curated Model Catalog</CardTitle>
              <CardDescription>Frontend product flows should use this catalog instead of provider discovery endpoints.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2">
              {data.model_catalog.map((model) => (
                <div key={composeModelValue(model.provider, model.model)} className="rounded-2xl border p-4">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{model.label}</h3>
                    <Badge variant={model.ready ? "success" : "warning"}>
                      {model.ready ? "Ready" : "Blocked"}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{model.description || model.reason}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{model.provider}</span>
                    <span>{model.model}</span>
                    {model.supports_structured_output && <span>Structured output</span>}
                    {model.supports_streaming && <span>Streaming</span>}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="fixed inset-x-0 bottom-2 z-30 px-3 sm:bottom-4 sm:px-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 rounded-xl border bg-background/95 p-3 shadow-lg backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted-foreground">
            `/settings` is now limited to provider configuration and workspace model defaults.
          </p>
          <div className="grid grid-cols-2 gap-2 sm:flex">
            <Button type="button" variant="outline" onClick={() => void refetch()} disabled={isFetching || mutation.isPending}>
              <RefreshCcw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending} className="col-span-2 sm:col-span-1">
              <Save className="h-4 w-4" />
              Save settings
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
