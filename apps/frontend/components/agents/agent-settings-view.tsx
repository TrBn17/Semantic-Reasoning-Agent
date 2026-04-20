"use client";

import { memo, startTransition, useDeferredValue, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCcw, Save, Shield, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { getAgentSettings, updateAgentSettings } from "@/lib/api/agents";
import {
  createAgentProfile,
  listAgentProfiles,
  setDefaultAgentProfile,
  updateAgentProfile,
} from "@/lib/api/agent-profiles";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import type {
  AgentSettingsResponse,
  AgentProfileResponse,
  ModelOption,
  ProviderConfigUpdate,
  TaskAssignmentUpdate,
} from "@/lib/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/src/shared/i18n/use-language";
import { readinessBadgeVariant } from "@/lib/badges/readiness";
import { composeProviderModel, parseProviderModelValue } from "@/lib/model-routing";

interface ProviderDraft {
  enabled: boolean;
  values: Record<string, string>;
}

type AgentProvider = AgentSettingsResponse["providers"][number];

function hydrateProviderDrafts(settings: AgentSettingsResponse): Record<string, ProviderDraft> {
  return Object.fromEntries(
    settings.providers.map((provider) => {
      const fieldByKey = Object.fromEntries(provider.fields.map((field) => [field.key, field]));
      return [
        provider.provider,
        {
          enabled: provider.enabled,
          values: Object.fromEntries(
            provider.values.map((value) => [
              value.key,
              value.source === "database" && !fieldByKey[value.key]?.secret
                ? value.masked_value
                : "",
            ]),
          ),
        },
      ] as const;
    }),
  );
}

function hydrateTaskDrafts(settings: AgentSettingsResponse): Record<string, string> {
  return Object.fromEntries(
    settings.task_assignments.map((task) => [
      task.task_type,
      composeProviderModel(task.provider, task.model),
    ]),
  );
}

function buildSettingsPayload(
  settings: AgentSettingsResponse,
  providerDrafts: Record<string, ProviderDraft>,
  taskDrafts: Record<string, string>,
): {
  providers: ProviderConfigUpdate[];
  task_assignments: TaskAssignmentUpdate[];
} {
  return {
    providers: settings.providers.map((provider) => ({
      provider: provider.provider,
      enabled: providerDrafts[provider.provider]?.enabled ?? provider.enabled,
      values: providerDrafts[provider.provider]?.values ?? {},
    })),
    task_assignments: settings.tasks
      .map((task) => {
        const value = taskDrafts[task.task_type];
        if (!value) return null;
        const [provider, model] = value.split("::");
        if (!provider || !model) return null;
        return { task_type: task.task_type, provider, model };
      })
      .filter(Boolean) as TaskAssignmentUpdate[],
  };
}

function getProviderPreview(provider: AgentProvider, draft?: ProviderDraft) {
  const enabled = draft?.enabled ?? provider.enabled;
  const draftValues = draft?.values ?? {};
  const missingFields = provider.fields
    .filter((field) => {
      const valueState = provider.values.find((item) => item.key === field.key);
      const currentValue = draftValues[field.key]?.trim();
      return !currentValue && !valueState?.configured && field.required;
    })
    .map((field) => field.key);
  const supportsRuntime = provider.supports_runtime;

  if (!enabled) {
    return {
      ready: false,
      reason: "Provider đang tắt.",
    };
  }
  if (missingFields.length > 0) {
    return {
      ready: false,
      reason: `Thiếu trường bắt buộc: ${missingFields.join(", ")}.`,
    };
  }
  if (!supportsRuntime) {
    return {
      ready: false,
      reason: "Model từ provider này hiện chưa dùng được cho tác vụ.",
    };
  }
  return {
    ready: true,
    reason: "Sẵn sàng sử dụng.",
  };
}

function getModelPreview(
  model: ModelOption,
  providerPreview: { ready: boolean; reason: string },
): ModelOption {
  if (!providerPreview.ready) {
    return {
      ...model,
      ready: false,
      reason: providerPreview.reason,
    };
  }
  if (!model.supports_runtime) {
    return {
      ...model,
      ready: false,
      reason: "Model này hiện chưa dùng được cho tác vụ.",
    };
  }
  return {
    ...model,
    ready: true,
    reason: "Sẵn sàng sử dụng.",
  };
}

interface TaskModelPickerProps {
  models: ModelOption[];
  value?: string;
  onChange: (value: string) => void;
  labels: {
    providerPlaceholder: string;
    allProviders: string;
    searchModelPlaceholder: string;
    selectModelPlaceholder: string;
    noModelMatch: string;
    assignmentUnavailable: string;
  };
}

const TaskModelPicker = memo(function TaskModelPicker({
  models,
  value,
  onChange,
  labels,
}: TaskModelPickerProps) {
  const selected = useMemo(
    () => models.find((item) => composeProviderModel(item.provider, item.model) === value),
    [models, value],
  );
  const providers = useMemo(
    () => Array.from(new Set(models.map((item) => item.provider))).sort((a, b) => a.localeCompare(b)),
    [models],
  );
  const [providerFilter, setProviderFilter] = useState<string>(selected?.provider ?? "all");
  const [searchText, setSearchText] = useState("");
  const deferredSearchText = useDeferredValue(searchText);

  useEffect(() => {
    const selectedValue = parseProviderModelValue(value);
    if (!selectedValue) {
      setProviderFilter("all");
      return;
    }
    setProviderFilter(selectedValue.provider);
  }, [value]);

  const filteredModels = useMemo(() => {
    const keyword = deferredSearchText.trim().toLowerCase();
    return models
      .filter((item) => {
        if (providerFilter !== "all" && item.provider !== providerFilter) {
          return false;
        }
        if (!keyword) {
          return true;
        }
        return (
          item.label.toLowerCase().includes(keyword) ||
          item.model.toLowerCase().includes(keyword) ||
          item.provider.toLowerCase().includes(keyword)
        );
      })
      .sort((a, b) => {
        if (a.ready !== b.ready) {
          return a.ready ? -1 : 1;
        }
        return a.label.localeCompare(b.label);
      });
  }, [deferredSearchText, models, providerFilter]);

  return (
    <div className="space-y-2">
      <div className="grid gap-2 md:grid-cols-[180px_minmax(0,1fr)]">
        <Select value={providerFilter} onValueChange={setProviderFilter}>
          <SelectTrigger>
            <SelectValue placeholder={labels.providerPlaceholder} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{labels.allProviders}</SelectItem>
            {providers.map((provider) => (
              <SelectItem key={provider} value={provider}>
                {provider}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          value={searchText}
          onChange={(event) =>
            startTransition(() => {
              setSearchText(event.target.value);
            })
          }
          placeholder={labels.searchModelPlaceholder}
        />
      </div>

      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={labels.selectModelPlaceholder} />
        </SelectTrigger>
        <SelectContent>
          {filteredModels.map((model) => (
            <SelectItem
              key={composeProviderModel(model.provider, model.model)}
              value={composeProviderModel(model.provider, model.model)}
            >
              {model.label} · {model.provider}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {filteredModels.length === 0 && (
        <p className="text-xs text-muted-foreground">
          {labels.noModelMatch}
        </p>
      )}
      {value && !selected && (
        <p className="text-xs text-amber-700">
          {labels.assignmentUnavailable}
        </p>
      )}
    </div>
  );
});

export function AgentSettingsView() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const preferredAgentProfileId = useWorkspaceStore((state) => state.preferredAgentProfileId);
  const setPreferredAgentProfileId = useWorkspaceStore(
    (state) => state.setPreferredAgentProfileId,
  );
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: queryKeys.agents.settings(workspaceId),
    queryFn: () => getAgentSettings(workspaceId),
  });
  const { data: profiles } = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });
  const [providerDrafts, setProviderDrafts] = useState<Record<string, ProviderDraft>>({});
  const [taskDrafts, setTaskDrafts] = useState<Record<string, string>>({});
  const [newProfileName, setNewProfileName] = useState("");
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profilePromptDraft, setProfilePromptDraft] = useState("");
  const [profileTaskDrafts, setProfileTaskDrafts] = useState<Record<string, string>>({});
  const [profileDescriptionDraft, setProfileDescriptionDraft] = useState("");
  const [profileAllowOverrideDraft, setProfileAllowOverrideDraft] = useState(true);
  const [catalogProviderFilter, setCatalogProviderFilter] = useState<string>("all");
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    if (!data) return;
    setProviderDrafts(hydrateProviderDrafts(data));
    setTaskDrafts(hydrateTaskDrafts(data));
  }, [data]);

  useEffect(() => {
    const selected =
      profiles?.find((item) => item.id === selectedProfileId) ??
      profiles?.find((item) => item.id === preferredAgentProfileId) ??
      profiles?.find((item) => item.is_default) ??
      profiles?.[0];
    if (!selected) return;
    setSelectedProfileId(selected.id);
    setPreferredAgentProfileId(selected.id);
    setProfilePromptDraft(selected.system_prompt);
    setProfileDescriptionDraft(selected.description);
    setProfileAllowOverrideDraft(selected.allow_chat_model_override);
    setProfileTaskDrafts(
      Object.fromEntries(
        selected.task_models.map((item) => [item.task_type, composeProviderModel(item.provider, item.model)]),
      ),
    );
  }, [preferredAgentProfileId, profiles, selectedProfileId, setPreferredAgentProfileId]);

  const modelLookup = useMemo(() => {
    const source = data?.models ?? [];
    return Object.fromEntries(
      source.map((item) => [composeProviderModel(item.provider, item.model), item]),
    );
  }, [data]);

  const catalogProviders = useMemo(
    () => Array.from(new Set((data?.models ?? []).map((item) => item.provider))).sort((a, b) => a.localeCompare(b)),
    [data?.models],
  );

  const catalogModels = useMemo(() => {
    const source = data?.models ?? [];
    if (catalogProviderFilter === "all") {
      return source;
    }
    return source.filter((item) => item.provider === catalogProviderFilter);
  }, [catalogProviderFilter, data?.models]);

  const providerPreviewByName = useMemo(() => {
    return Object.fromEntries(
      (data?.providers ?? []).map((provider) => [
        provider.provider,
        getProviderPreview(provider, providerDrafts[provider.provider]),
      ]),
    );
  }, [data?.providers, providerDrafts]);

  const modelPreviewLookup = useMemo(() => {
    return Object.fromEntries(
      (data?.models ?? []).map((model) => {
        const providerPreview = providerPreviewByName[model.provider] ?? {
          ready: model.ready,
          reason: model.reason,
        };
        const preview = getModelPreview(model, providerPreview);
        return [composeProviderModel(preview.provider, preview.model), preview];
      }),
    );
  }, [data?.models, providerPreviewByName]);

  const hasPendingSettingsChanges = useMemo(() => {
    if (!data) return false;
    const baseline = buildSettingsPayload(
      data,
      hydrateProviderDrafts(data),
      hydrateTaskDrafts(data),
    );
    const current = buildSettingsPayload(data, providerDrafts, taskDrafts);
    return JSON.stringify(current) !== JSON.stringify(baseline);
  }, [data, providerDrafts, taskDrafts]);

  const mutation = useMutation({
    mutationFn: (payload: {
      providers: ProviderConfigUpdate[];
      task_assignments: TaskAssignmentUpdate[];
    }) =>
      updateAgentSettings({
        workspace_id: data?.workspace_id ?? workspaceId ?? "workspace-demo",
        ...payload,
      }),
    onSuccess: async (updated) => {
      queryClient.setQueryData(queryKeys.agents.settings(workspaceId), updated);
      setProviderDrafts(hydrateProviderDrafts(updated));
      setTaskDrafts(hydrateTaskDrafts(updated));
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.settings(workspaceId) });
      toast.success(t.agentsSettings.toasts.agentSettingsSaved);
    },
    onError: (err) =>
      toast.error(`${t.agentsSettings.toasts.saveFailedPrefix} ${(err as Error).message}`),
  });

  const createProfileMutation = useMutation({
    mutationFn: () =>
      createAgentProfile({
        workspace_id: data?.workspace_id ?? workspaceId ?? "workspace-demo",
        name: newProfileName.trim(),
        description: "",
        system_prompt: "",
        allow_chat_model_override: true,
        task_models: data?.task_assignments.map((item) => ({
          task_type: item.task_type,
          provider: item.provider,
          model: item.model,
        })) ?? [],
      }),
    onSuccess: (profile) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      setNewProfileName("");
      setSelectedProfileId(profile.id);
      setPreferredAgentProfileId(profile.id);
      toast.success(t.agentsSettings.toasts.agentProfileCreated);
    },
    onError: (err) =>
      toast.error(`${t.agentsSettings.toasts.createFailedPrefix} ${(err as Error).message}`),
  });

  const saveProfileMutation = useMutation({
    mutationFn: (profile: AgentProfileResponse) =>
      updateAgentProfile(profile.id, {
        description: profileDescriptionDraft,
        system_prompt: profilePromptDraft,
        allow_chat_model_override: profileAllowOverrideDraft,
        task_models: data?.tasks.map((task) => {
          const value = profileTaskDrafts[task.task_type];
          const [provider, model] = value?.split("::") ?? [];
          return {
            task_type: task.task_type,
            provider: provider ?? profile.task_models.find((item) => item.task_type === task.task_type)?.provider ?? "echo",
            model: model ?? profile.task_models.find((item) => item.task_type === task.task_type)?.model ?? "local-echo",
          };
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success(t.agentsSettings.toasts.profileSaved);
    },
    onError: (err) =>
      toast.error(`${t.agentsSettings.toasts.profileSaveFailedPrefix} ${(err as Error).message}`),
  });

  const setDefaultMutation = useMutation({
    mutationFn: (profileId: string) => setDefaultAgentProfile(profileId),
    onSuccess: (profile) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      setPreferredAgentProfileId(profile.id);
      toast.success(t.agentsSettings.toasts.defaultProfileUpdated);
    },
    onError: (err) =>
      toast.error(`${t.agentsSettings.toasts.defaultUpdateFailedPrefix} ${(err as Error).message}`),
  });

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  const handleSaveSettings = () => {
    mutation.mutate(buildSettingsPayload(data, providerDrafts, taskDrafts));
  };

  const showFloatingActions = hasPendingSettingsChanges;

  return (
    <div className="space-y-4 pb-20 sm:space-y-6 sm:pb-24">
      {showFloatingActions && (
        <div className="fixed inset-x-0 bottom-2 z-30 px-3 sm:bottom-3 sm:px-6">
          <div className="mx-auto max-w-3xl rounded-lg border bg-background/94 px-3 py-2 shadow-md backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <p className="min-w-0 truncate text-[11px] text-muted-foreground sm:text-xs">
                {t.agentsSettings.builder.description}
              </p>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced((current) => !current)}
                className="h-7 shrink-0 px-2 text-[11px] sm:text-xs"
              >
                {showAdvanced
                  ? t.agentsSettings.builder.hideAdvanced
                  : t.agentsSettings.builder.showAdvanced}
              </Button>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void refetch()}
                  disabled={isFetching || mutation.isPending}
                  className="h-8 w-full text-xs"
                >
                  <RefreshCcw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
                  {t.agentsSettings.builder.refreshCatalog}
                </Button>
                <Button
                  onClick={handleSaveSettings}
                  disabled={mutation.isPending || !hasPendingSettingsChanges}
                  className="h-8 w-full text-xs"
                >
                  <Save className="h-4 w-4" />
                  {t.agentsSettings.builder.saveSettings}
                </Button>
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t.agentsSettings.builder.title}</CardTitle>
          <CardDescription>
            {t.agentsSettings.builder.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          {t.agentsSettings.builder.minimalHint}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t.agentsSettings.providerEnv.title}</CardTitle>
          <CardDescription>
            {t.agentsSettings.providerEnv.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.providers.map((provider) => {
            const draft = providerDrafts[provider.provider];
            const providerPreview = providerPreviewByName[provider.provider] ?? getProviderPreview(provider, draft);
            return (
              <div key={provider.provider} className="rounded-xl border p-3 sm:p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{provider.label}</h3>
                      <Badge variant={readinessBadgeVariant(providerPreview.ready)}>
                        {providerPreview.ready
                          ? t.agentsSettings.taskRouting.ready
                          : t.agentsSettings.providerEnv.needsSetup}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {providerPreview.reason}
                    </p>
                  </div>
                  <Button
                    variant={draft?.enabled === false ? "outline" : "secondary"}
                    size="sm"
                    onClick={() =>
                      setProviderDrafts((current) => ({
                        ...current,
                        [provider.provider]: {
                          enabled: !(current[provider.provider]?.enabled ?? provider.enabled),
                          values: current[provider.provider]?.values ?? {},
                        },
                      }))
                    }
                  >
                    {(draft?.enabled ?? provider.enabled)
                      ? t.agentsSettings.providerEnv.enabled
                      : t.agentsSettings.providerEnv.disabled}
                  </Button>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {provider.fields.length === 0 && (
                    <div className="text-sm text-muted-foreground">
                      {t.agentsSettings.providerEnv.noAdditionalEnv}
                    </div>
                  )}
                  {provider.fields.map((field) => {
                    const valueState = provider.values.find((item) => item.key === field.key);
                    const currentValue = draft?.values[field.key] ?? "";
                    const placeholder =
                      currentValue ? field.placeholder : valueState?.masked_value || field.placeholder;
                    return (
                      <div key={field.key} className="space-y-2">
                        <Label htmlFor={`${provider.provider}-${field.key}`}>
                          {field.label}
                          {!field.required ? " (optional)" : ""}
                        </Label>
                        {field.input_type === "select" ? (
                          <Select
                            value={currentValue || valueState?.masked_value || field.placeholder}
                            onValueChange={(value) =>
                              setProviderDrafts((current) => ({
                                ...current,
                                [provider.provider]: {
                                  enabled: current[provider.provider]?.enabled ?? provider.enabled,
                                  values: {
                                    ...(current[provider.provider]?.values ?? {}),
                                    [field.key]: value,
                                  },
                                },
                              }))
                            }
                          >
                            <SelectTrigger id={`${provider.provider}-${field.key}`}>
                              <SelectValue placeholder={field.placeholder} />
                            </SelectTrigger>
                            <SelectContent>
                              {field.options.map((option) => (
                                <SelectItem key={option} value={option}>
                                  {option}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            id={`${provider.provider}-${field.key}`}
                            type={field.secret ? "password" : "text"}
                            value={currentValue}
                            placeholder={placeholder}
                            onChange={(event) =>
                              setProviderDrafts((current) => ({
                                ...current,
                                [provider.provider]: {
                                  enabled: current[provider.provider]?.enabled ?? provider.enabled,
                                  values: {
                                    ...(current[provider.provider]?.values ?? {}),
                                    [field.key]: event.target.value,
                                  },
                                },
                              }))
                            }
                          />
                        )}
                        <p className="text-xs text-muted-foreground">
                          {valueState?.configured
                            ? `${t.agentsSettings.providerEnv.currentPrefix} ${valueState.masked_value}`
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

      <Card>
        <CardHeader>
          <CardTitle>{t.agentsSettings.profiles.title}</CardTitle>
          <CardDescription>
            {t.agentsSettings.profiles.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 sm:flex sm:flex-wrap">
            <Input
              value={newProfileName}
              onChange={(event) => setNewProfileName(event.target.value)}
              placeholder={t.agentsSettings.profiles.newProfileNamePlaceholder}
              className="w-full sm:max-w-sm"
            />
            <Button
              onClick={() => createProfileMutation.mutate()}
              disabled={createProfileMutation.isPending || !newProfileName.trim()}
              className="w-full sm:w-auto"
            >
              <Sparkles className="h-4 w-4" />
              {t.agentsSettings.profiles.createProfile}
            </Button>
          </div>

          <div className="grid items-start gap-3 sm:gap-4 xl:grid-cols-[260px_minmax(0,1fr)]">
            <div className="space-y-2 xl:max-h-[560px] xl:overflow-y-auto xl:pr-1">
              {(profiles ?? []).map((profile) => (
                <button
                  key={profile.id}
                  type="button"
                  onClick={() => {
                    setSelectedProfileId(profile.id);
                    setPreferredAgentProfileId(profile.id);
                    setProfilePromptDraft(profile.system_prompt);
                    setProfileDescriptionDraft(profile.description);
                    setProfileAllowOverrideDraft(profile.allow_chat_model_override);
                    setProfileTaskDrafts(
                      Object.fromEntries(
                        profile.task_models.map((item) => [
                          item.task_type,
                          composeProviderModel(item.provider, item.model),
                        ]),
                      ),
                    );
                  }}
                  className={`w-full rounded-xl border p-3 text-left transition sm:p-4 ${
                    selectedProfileId === profile.id
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "hover:border-primary/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{profile.name}</span>
                    {profile.is_default && <Badge variant="success">{t.agentsSettings.profiles.defaultBadge}</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{profile.description || t.agentsSettings.profiles.noDescription}</p>
                </button>
              ))}
            </div>

            {(() => {
              const selectedProfile = (profiles ?? []).find((item) => item.id === selectedProfileId);
              if (!selectedProfile) {
                return <div className="rounded-xl border p-4 text-sm text-muted-foreground">{t.agentsSettings.profiles.noProfileSelected}</div>;
              }
              return (
                <div className="space-y-5 rounded-xl border p-4 sm:p-5">
                  <div className="space-y-1">
                    <div>
                      <h3 className="font-semibold">{selectedProfile.name}</h3>
                      <p className="text-sm text-muted-foreground">{t.agentsSettings.profiles.panelDescription}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile-description">{t.agentsSettings.profiles.descriptionLabel}</Label>
                    <Input
                      id="profile-description"
                      value={profileDescriptionDraft}
                      onChange={(event) => setProfileDescriptionDraft(event.target.value)}
                      placeholder={t.agentsSettings.profiles.descriptionPlaceholder}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile-prompt">{t.agentsSettings.profiles.systemPromptLabel}</Label>
                    <Textarea
                      id="profile-prompt"
                      value={profilePromptDraft}
                      onChange={(event) => setProfilePromptDraft(event.target.value)}
                      placeholder={t.agentsSettings.profiles.systemPromptPlaceholder}
                      className="min-h-[140px]"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={profileAllowOverrideDraft}
                      onChange={(event) => setProfileAllowOverrideDraft(event.target.checked)}
                    />
                    {t.agentsSettings.profiles.allowChatOverride}
                  </label>
                  <div className="space-y-3">
                    {showAdvanced &&
                      data.tasks.map((task) => (
                        <div key={task.task_type} className="grid gap-2 md:grid-cols-[200px_1fr] md:items-center">
                          <div>
                            <div className="font-medium">{task.label}</div>
                            <div className="text-xs text-muted-foreground">{task.description}</div>
                          </div>
                          <TaskModelPicker
                            models={data.models}
                            value={profileTaskDrafts[task.task_type]}
                            labels={t.agentsSettings.picker}
                            onChange={(value) =>
                              setProfileTaskDrafts((current) => ({ ...current, [task.task_type]: value }))
                            }
                          />
                        </div>
                      ))}
                  </div>
                  <div className="sticky bottom-0 -mx-4 border-t bg-background/95 px-4 py-3 backdrop-blur sm:-mx-5 sm:px-5">
                    <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
                      <Button
                        variant="outline"
                        onClick={() => setDefaultMutation.mutate(selectedProfile.id)}
                        disabled={setDefaultMutation.isPending || selectedProfile.is_default}
                        className="w-full sm:w-auto"
                      >
                        <Shield className="h-4 w-4" />
                        {t.agentsSettings.profiles.setDefault}
                      </Button>
                      <Button
                        onClick={() => saveProfileMutation.mutate(selectedProfile)}
                        disabled={saveProfileMutation.isPending}
                        className="w-full sm:w-auto"
                      >
                        <Save className="h-4 w-4" />
                        {t.agentsSettings.profiles.saveProfile}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </CardContent>
      </Card>

      {showAdvanced && <Card>
        <CardHeader>
          <CardTitle>{t.agentsSettings.taskRouting.title}</CardTitle>
          <CardDescription>
            {t.agentsSettings.taskRouting.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.tasks.map((task) => {
            const selectedValue = taskDrafts[task.task_type];
            const selectedModel = selectedValue ? modelPreviewLookup[selectedValue] ?? null : null;
            return (
              <div
                key={task.task_type}
                className="rounded-xl border p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="font-semibold">{task.label}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {task.description}
                    </p>
                  </div>
                  {selectedModel && (
                    <Badge variant={readinessBadgeVariant(selectedModel.ready)}>
                      {selectedModel.ready
                        ? t.agentsSettings.taskRouting.ready
                        : t.agentsSettings.taskRouting.blocked}
                    </Badge>
                  )}
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,320px)_1fr]">
                  <TaskModelPicker
                    models={data.models}
                    value={selectedValue}
                    labels={t.agentsSettings.picker}
                    onChange={(value) =>
                      setTaskDrafts((current) => ({ ...current, [task.task_type]: value }))
                    }
                  />
                  <div className="rounded-lg bg-muted/20 p-4 text-sm">
                    {selectedModel ? (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {selectedModel.label} ({selectedModel.provider})
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">{selectedModel.reason}</p>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">
                        {t.agentsSettings.taskRouting.noModelSelected}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>}

      {showAdvanced && <Card>
        <CardHeader>
          <CardTitle>{t.agentsSettings.modelCatalog.title}</CardTitle>
          <CardDescription>
            {t.agentsSettings.modelCatalog.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          <div className="lg:col-span-2 flex flex-wrap gap-2">
            <Button
              type="button"
              variant={catalogProviderFilter === "all" ? "secondary" : "outline"}
              size="sm"
              onClick={() => setCatalogProviderFilter("all")}
            >
              {t.agentsSettings.modelCatalog.allProviders}
            </Button>
            {catalogProviders.map((provider) => (
              <Button
                key={provider}
                type="button"
                variant={catalogProviderFilter === provider ? "secondary" : "outline"}
                size="sm"
                onClick={() => setCatalogProviderFilter(provider)}
              >
                {provider}
              </Button>
            ))}
          </div>
          {catalogModels.map((model) => {
            const preview = modelPreviewLookup[composeProviderModel(model.provider, model.model)] ?? model;
            return (
              <div key={composeProviderModel(model.provider, model.model)} className="rounded-xl border p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-semibold">{preview.label}</h3>
                  <Badge variant={readinessBadgeVariant(preview.ready)}>
                    {preview.ready
                      ? t.agentsSettings.modelCatalog.ready
                      : t.agentsSettings.modelCatalog.blocked}
                  </Badge>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant="outline">{preview.provider}</Badge>
                  <Badge variant="outline">{preview.model}</Badge>
                </div>
              </div>
            );
          })}
          {catalogModels.length === 0 && (
            <div className="lg:col-span-2 rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
              {t.agentsSettings.modelCatalog.noModelsForFilter}
            </div>
          )}
        </CardContent>
      </Card>}
    </div>
  );
}
