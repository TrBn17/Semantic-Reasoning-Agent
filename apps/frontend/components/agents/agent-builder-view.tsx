"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCircle2, Play, Save, Settings2, Sparkles, Star } from "lucide-react";
import { toast } from "sonner";
import { LoadingLink as Link } from "@/components/navigation/loading-link";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  createAgentProfile,
  listAgentProfiles,
  setDefaultAgentProfile,
  updateAgentProfile,
} from "@/lib/api/agent-profiles";
import { getAgentSettings, updateAgentSettings } from "@/lib/api/agents";
import { resolveTask } from "@/lib/api/tasks";
import { readinessBadgeVariant } from "@/lib/badges/readiness";
import { composeProviderModel, parseProviderModelValue } from "@/lib/model-routing";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import type {
  AgentSettingsResponse,
  AgentProfileResponse,
  AgentProfileTaskModelAssignment,
  ModelOption,
  TaskAssignmentResponse,
  TaskDefinition,
  TaskResolutionResponse,
} from "@/lib/api/types";
import { cn, formatDateTime } from "@/lib/utils";
import { useI18n } from "@/src/shared/i18n/use-language";

type ProfileDraft = {
  name: string;
  description: string;
  systemPrompt: string;
  allowChatOverride: boolean;
  taskModels: Record<string, string>;
};

type ProviderDraft = {
  enabled: boolean;
  values: Record<string, string>;
};

const NEW_PROFILE_ID = "__new__";

function hydrateProviderDrafts(
  providers: AgentSettingsResponse["providers"],
): Record<string, ProviderDraft> {
  return Object.fromEntries(
    providers.map((provider) => [
      provider.provider,
      {
        enabled: provider.enabled,
        values: {},
      },
    ]),
  );
}

function profileToDraft(
  profile: AgentProfileResponse | null,
  workspaceAssignments: TaskAssignmentResponse[],
): ProfileDraft {
  return {
    name: profile?.name ?? "New agent",
    description: profile?.description ?? "",
    systemPrompt: profile?.system_prompt ?? "",
    allowChatOverride: profile?.allow_chat_model_override ?? true,
    taskModels: Object.fromEntries(
      workspaceAssignments.map((assignment) => {
        const profileAssignment = profile?.task_models.find(
          (item) => item.task_type === assignment.task_type,
        );
        return [
          assignment.task_type,
          composeProviderModel(
            profileAssignment?.provider ?? assignment.provider,
            profileAssignment?.model ?? assignment.model,
          ),
        ] as const;
      }),
    ),
  };
}

export function AgentBuilderView() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId) ?? "workspace-demo";
  const [selectedProfileId, setSelectedProfileId] = useState<string>(NEW_PROFILE_ID);
  const [draft, setDraft] = useState<ProfileDraft | null>(null);
  const [providerDrafts, setProviderDrafts] = useState<Record<string, ProviderDraft>>({});
  const [testPrompt, setTestPrompt] = useState("");
  const [useRetrieval, setUseRetrieval] = useState(true);
  const [testResult, setTestResult] = useState<TaskResolutionResponse | null>(null);

  const settingsQuery = useQuery({
    queryKey: queryKeys.agents.settings(workspaceId),
    queryFn: () => getAgentSettings(workspaceId),
  });
  const profilesQuery = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });

  const profiles = useMemo(() => profilesQuery.data ?? [], [profilesQuery.data]);
  const workspaceAssignments = useMemo(
    () => settingsQuery.data?.task_assignments ?? [],
    [settingsQuery.data?.task_assignments],
  );
  const tasks = useMemo(() => settingsQuery.data?.tasks ?? [], [settingsQuery.data?.tasks]);
  const models = useMemo(() => settingsQuery.data?.models ?? [], [settingsQuery.data?.models]);
  const selectedProfile =
    profiles.find((profile) => profile.id === selectedProfileId) ?? null;

  useEffect(() => {
    if (!settingsQuery.data || !profilesQuery.data) return;
    const fallbackProfile =
      profilesQuery.data.find((profile) => profile.is_default) ??
      profilesQuery.data[0] ??
      null;
    const nextSelected =
      selectedProfileId === NEW_PROFILE_ID
        ? fallbackProfile?.id ?? NEW_PROFILE_ID
        : selectedProfileId;
    setSelectedProfileId(nextSelected);
  }, [profilesQuery.data, selectedProfileId, settingsQuery.data]);

  useEffect(() => {
    if (!settingsQuery.data) return;
    setProviderDrafts(hydrateProviderDrafts(settingsQuery.data.providers));
  }, [settingsQuery.data]);

  useEffect(() => {
    if (!settingsQuery.data) return;
    setDraft(profileToDraft(selectedProfile, workspaceAssignments));
  }, [selectedProfile, settingsQuery.data, workspaceAssignments]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!draft) throw new Error(t.common.serviceUnavailable);
      const taskModels = Object.entries(draft.taskModels)
        .map(([taskType, value]) => {
          const parsed = parseProviderModelValue(value);
          if (!parsed) return null;
          return {
            task_type: taskType,
            provider: parsed.provider,
            model: parsed.model,
          } satisfies AgentProfileTaskModelAssignment;
        })
        .filter((item): item is AgentProfileTaskModelAssignment => item !== null);

      if (!selectedProfile) {
        return createAgentProfile({
          workspace_id: workspaceId,
          name: draft.name,
          description: draft.description,
          system_prompt: draft.systemPrompt,
          allow_chat_model_override: draft.allowChatOverride,
          task_models: taskModels,
        });
      }

      return updateAgentProfile(selectedProfile.id, {
        name: draft.name,
        description: draft.description,
        system_prompt: draft.systemPrompt,
        allow_chat_model_override: draft.allowChatOverride,
        task_models: taskModels,
      });
    },
    onSuccess: async (profile) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      setSelectedProfileId(profile.id);
      toast.success(t.agentsSettings.toasts.profileSaved);
    },
    onError: (error) =>
      toast.error(`${t.agentsSettings.toasts.profileSaveFailedPrefix} ${(error as Error).message}`),
  });

  const providerSaveMutation = useMutation({
    mutationFn: async () => {
      if (!settingsQuery.data) throw new Error(t.common.serviceUnavailable);
      return updateAgentSettings({
        workspace_id: workspaceId,
        providers: settingsQuery.data.providers.map((provider) => ({
          provider: provider.provider,
          enabled: providerDrafts[provider.provider]?.enabled ?? provider.enabled,
          values: providerDrafts[provider.provider]?.values ?? {},
        })),
        task_assignments: settingsQuery.data.task_assignments.map((assignment) => ({
          task_type: assignment.task_type,
          provider: assignment.provider,
          model: assignment.model,
        })),
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.settings(workspaceId) });
      toast.success(t.agentsSettings.toasts.agentSettingsSaved);
    },
    onError: (error) =>
      toast.error(`${t.agentsSettings.toasts.saveFailedPrefix} ${(error as Error).message}`),
  });

  const defaultMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProfile) throw new Error(t.common.serviceUnavailable);
      return setDefaultAgentProfile(selectedProfile.id);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success(t.agentsSettings.toasts.defaultProfileUpdated);
    },
    onError: (error) =>
      toast.error(`${t.agentsSettings.toasts.defaultUpdateFailedPrefix} ${(error as Error).message}`),
  });

  const testMutation = useMutation({
    mutationFn: async () => {
      const chatAssignment = parseProviderModelValue(draft?.taskModels.chat);
      return resolveTask({
        entrypoint: "chat",
        content: testPrompt,
        workspace_id: workspaceId,
        task_type: "chat",
        requested_output: "answer",
        provider: chatAssignment?.provider,
        model: chatAssignment?.model,
        use_retrieval: useRetrieval,
      });
    },
    onSuccess: async (result) => {
      setTestResult(result);
      await queryClient.invalidateQueries({ queryKey: queryKeys.tasks.list() });
      toast.success(t.agentsPage.testAgent);
    },
    onError: (error) => toast.error(`${t.common.invokeFailed} ${(error as Error).message}`),
  });

  const chatModel = useMemo(() => {
    const selected = parseProviderModelValue(draft?.taskModels.chat);
    if (!selected) return null;
    return (
      models.find(
        (model) => model.provider === selected.provider && model.model === selected.model,
      ) ?? null
    );
  }, [draft?.taskModels.chat, models]);

  const providerSetupComplete = useMemo(
    () => (settingsQuery.data?.providers ?? []).some((provider) => provider.enabled && provider.ready),
    [settingsQuery.data?.providers],
  );

  const hasProviderDraftChanges = useMemo(() => {
    const providers = settingsQuery.data?.providers ?? [];
    if (providers.length === 0) return false;
    return providers.some((provider) => {
      const draftState = providerDrafts[provider.provider];
      if (!draftState) return false;
      if (draftState.enabled !== provider.enabled) return true;
      return Object.values(draftState.values).some((value) => value.trim().length > 0);
    });
  }, [providerDrafts, settingsQuery.data?.providers]);

  const readiness = {
    hasName: Boolean(draft?.name.trim()),
    hasPrompt: Boolean(draft?.systemPrompt.trim()),
    hasChatRouting: Boolean(parseProviderModelValue(draft?.taskModels.chat)),
    chatReady: chatModel?.ready ?? false,
  };
  const completionScore = Object.values(readiness).filter(Boolean).length;

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-6 py-8">
      <section className="surface-panel-strong hero-panel overflow-hidden px-6 py-6 lg:px-8">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_360px] lg:items-end">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-primary/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.22em] text-primary">
              <Sparkles className="h-3.5 w-3.5" />
              {t.agentsPage.heroBadge}
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-foreground">
                {t.agentsPage.title}
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-base">
                {t.agentsPage.subtitle}
              </p>
            </div>
          </div>
          <Card className="border-primary/15 bg-background/70 shadow-none">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">{t.agentsPage.readinessTitle}</CardTitle>
              <CardDescription>{t.agentsPage.readinessDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-end justify-between">
                <div className="text-4xl font-semibold">{completionScore}/4</div>
                <Badge variant={completionScore >= 3 ? "success" : "warning"}>
                  {completionScore >= 3 ? t.agentsPage.readyToReview : t.agentsPage.needsSetup}
                </Badge>
              </div>
              <div className="grid gap-2 text-sm">
                <StatusLine label={t.agentsPage.profileName} ready={readiness.hasName} />
                <StatusLine label={t.agentsPage.systemPrompt} ready={readiness.hasPrompt} />
                <StatusLine label={t.agentsPage.chatRouting} ready={readiness.hasChatRouting} />
                <StatusLine label={t.agentsPage.chatModelReady} ready={readiness.chatReady} />
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1.2fr)_360px]">
        <Card id="provider-setup" className="surface-panel xl:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">{t.agentsSettings.providerEnv.title}</CardTitle>
            <CardDescription>{t.agentsSettings.providerEnv.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(settingsQuery.data?.providers ?? []).map((provider) => {
              const draftState = providerDrafts[provider.provider] ?? {
                enabled: provider.enabled,
                values: {},
              };
              return (
                <div key={provider.provider} className="rounded-xl border p-3 sm:p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{provider.label}</h3>
                        <Badge variant={readinessBadgeVariant(provider.enabled && provider.ready)}>
                          {provider.enabled && provider.ready
                            ? t.agentsSettings.taskRouting.ready
                            : t.agentsSettings.providerEnv.needsSetup}
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{provider.reason}</p>
                    </div>
                    <Button
                      variant={draftState.enabled ? "secondary" : "outline"}
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
                      {draftState.enabled
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
                      const currentValue = draftState.values[field.key] ?? "";
                      const placeholder =
                        currentValue || field.input_type === "select"
                          ? field.placeholder
                          : valueState?.masked_value || field.placeholder;
                      return (
                        <div key={field.key} className="space-y-2">
                          <Label htmlFor={`${provider.provider}-${field.key}`}>
                            {field.label}
                            {!field.required ? " (optional)" : ""}
                          </Label>
                          {field.input_type === "select" ? (
                            <Select
                              value={currentValue}
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

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-muted/20 px-3 py-2">
              <p className="text-xs text-muted-foreground">{t.agentsSettings.builder.minimalHint}</p>
              <Button
                onClick={() => providerSaveMutation.mutate()}
                disabled={providerSaveMutation.isPending || !hasProviderDraftChanges}
              >
                <Save className="h-4 w-4" />
                {t.agentsSettings.builder.saveSettings}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="surface-panel h-fit">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">{t.agentsPage.catalogTitle}</CardTitle>
                <CardDescription>{t.agentsPage.catalogDescription}</CardDescription>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSelectedProfileId(NEW_PROFILE_ID);
                  setDraft(profileToDraft(null, workspaceAssignments));
                }}
              >
                {t.agentsPage.new}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {(profilesQuery.isLoading || settingsQuery.isLoading) && (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton key={index} className="h-20 w-full rounded-2xl" />
                ))}
              </div>
            )}
            {!profilesQuery.isLoading && (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedProfileId(NEW_PROFILE_ID);
                    setDraft(profileToDraft(null, workspaceAssignments));
                  }}
                  className={cn(
                    "w-full rounded-2xl border px-4 py-4 text-left transition-all",
                    selectedProfileId === NEW_PROFILE_ID
                      ? "border-primary/40 bg-primary/5 shadow-sm"
                      : "border-border hover:border-primary/25 hover:bg-accent/30",
                  )}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-medium">{t.agentsPage.newDraftTitle}</div>
                      <div className="text-xs text-muted-foreground">
                        {t.agentsPage.newDraftDescription}
                      </div>
                    </div>
                    <Badge variant="info">{t.agentsPage.draft}</Badge>
                  </div>
                </button>
                {profiles.map((profile) => (
                  <button
                    key={profile.id}
                    type="button"
                    onClick={() => setSelectedProfileId(profile.id)}
                    className={cn(
                      "w-full rounded-2xl border px-4 py-4 text-left transition-all",
                      selectedProfileId === profile.id
                        ? "border-primary/40 bg-primary/5 shadow-sm"
                        : "border-border hover:border-primary/25 hover:bg-accent/30",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate font-medium">{profile.name}</div>
                        <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                          {profile.description || t.agentsPage.noDescription}
                        </div>
                      </div>
                      {profile.is_default && (
                        <Badge variant="success" className="shrink-0">
                          {t.agentsPage.default}
                        </Badge>
                      )}
                    </div>
                  </button>
                ))}
              </>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="surface-panel overflow-hidden">
            <CardHeader className="border-b border-border/60 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base">
                    {selectedProfile ? selectedProfile.name : t.agentsPage.newDraftTitle}
                  </CardTitle>
                  <CardDescription>{t.agentsPage.builderDescription}</CardDescription>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedProfile && !selectedProfile.is_default && (
                    <Button
                      variant="secondary"
                      onClick={() => defaultMutation.mutate()}
                      disabled={defaultMutation.isPending}
                    >
                      <Star className="h-4 w-4" />
                      {t.agentsPage.makeDefault}
                    </Button>
                  )}
                  <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || !draft}>
                    <Save className="h-4 w-4" />
                    {t.agentsPage.saveAgent}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {draft ? (
                <Tabs defaultValue="identity" className="w-full">
                  <div className="border-b border-border/60 px-6 py-3">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="identity">{t.agentsPage.tabIdentity}</TabsTrigger>
                      <TabsTrigger value="behavior">{t.agentsPage.tabBehavior}</TabsTrigger>
                      <TabsTrigger value="routing">{t.agentsPage.tabRouting}</TabsTrigger>
                      <TabsTrigger value="preview">{t.agentsPage.tabPreview}</TabsTrigger>
                    </TabsList>
                  </div>

                  <TabsContent value="identity" className="mt-0 px-6 py-6">
                    <div className="grid gap-5">
                      <div className="grid gap-2">
                        <Label htmlFor="agent-name">{t.agentsPage.agentName}</Label>
                        <Input
                          id="agent-name"
                          value={draft.name}
                          onChange={(event) =>
                            setDraft((current) =>
                              current ? { ...current, name: event.target.value } : current,
                            )
                          }
                          placeholder={t.agentsPage.agentNamePlaceholder}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="agent-description">{t.agentsPage.roleSummary}</Label>
                        <Textarea
                          id="agent-description"
                          value={draft.description}
                          onChange={(event) =>
                            setDraft((current) =>
                              current ? { ...current, description: event.target.value } : current,
                            )
                          }
                          placeholder={t.agentsPage.roleSummaryPlaceholder}
                          className="min-h-28"
                        />
                      </div>
                      <label className="flex items-center gap-3 rounded-2xl border border-border/70 bg-muted/20 px-4 py-3 text-sm">
                        <input
                          type="checkbox"
                          checked={draft.allowChatOverride}
                          onChange={(event) =>
                            setDraft((current) =>
                              current
                                ? { ...current, allowChatOverride: event.target.checked }
                                : current,
                            )
                          }
                        />
                        {t.agentsPage.allowOverride}
                      </label>
                    </div>
                  </TabsContent>

                  <TabsContent value="behavior" className="mt-0 px-6 py-6">
                    <div className="grid gap-3">
                      <Label htmlFor="agent-prompt">{t.agentsPage.systemPrompt}</Label>
                      <Textarea
                        id="agent-prompt"
                        value={draft.systemPrompt}
                        onChange={(event) =>
                          setDraft((current) =>
                            current ? { ...current, systemPrompt: event.target.value } : current,
                          )
                        }
                        placeholder={t.agentsPage.promptPlaceholder}
                        className="min-h-[260px]"
                      />
                      <p className="text-xs leading-5 text-muted-foreground">
                        {t.agentsPage.promptHint}
                      </p>
                    </div>
                  </TabsContent>

                  <TabsContent value="routing" className="mt-0 px-6 py-6">
                    <div className="grid gap-4">
                      {!providerSetupComplete && (
                        <div className="rounded-2xl border border-amber-300/60 bg-amber-50/70 p-4 text-sm text-amber-900">
                          {t.agentsSettings.providerEnv.description}
                        </div>
                      )}
                      {tasks.map((task) => (
                        <RoutingCard
                          key={task.task_type}
                          task={task}
                          models={providerSetupComplete ? models : []}
                          value={draft.taskModels[task.task_type] ?? ""}
                          setupRequired={!providerSetupComplete}
                          onChange={(value) =>
                            setDraft((current) =>
                              current
                                ? {
                                    ...current,
                                    taskModels: {
                                      ...current.taskModels,
                                      [task.task_type]: value,
                                    },
                                  }
                                : current,
                            )
                          }
                        />
                      ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="preview" className="mt-0 px-6 py-6">
                    <div className="grid gap-4 lg:grid-cols-2">
                      <PreviewPanel
                        draft={draft}
                        chatModel={chatModel}
                        selectedProfile={selectedProfile}
                      />
                      <Card className="border-border/70 shadow-none">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm">{t.agentsSettings.providerEnv.title}</CardTitle>
                          <CardDescription>{t.agentsSettings.providerEnv.description}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3 text-sm text-muted-foreground">
                          <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                            {t.agentsSettings.builder.minimalHint}
                          </div>
                          <Link href="#provider-setup" className="inline-flex items-center gap-2 text-primary hover:underline">
                            <Settings2 className="h-4 w-4" />
                            {t.agentsSettings.providerEnv.title}
                          </Link>
                        </CardContent>
                      </Card>
                    </div>
                  </TabsContent>
                </Tabs>
              ) : (
                <div className="space-y-3 px-6 py-6">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-40 w-full" />
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card variant="surface">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{t.agentsPage.livePreviewTitle}</CardTitle>
              <CardDescription>{t.agentsPage.livePreviewDescription}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl border border-border/70 bg-muted/20 p-4">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-primary/10 p-2 text-primary">
                    <Bot className="h-5 w-5" />
                  </div>
                  <div className="space-y-1">
                    <div className="font-medium">{draft?.name || t.agentsPage.newDraftTitle}</div>
                    <div className="text-sm text-muted-foreground">
                      {draft?.description || t.agentsPage.roleSummaryPlaceholder}
                    </div>
                  </div>
                </div>
              </div>
              <div className="grid gap-2 text-sm">
                <StatusLine
                  label={t.agentsPage.chatRouting}
                  ready={Boolean(chatModel)}
                  detail={
                    providerSetupComplete
                      ? chatModel
                        ? `${chatModel.provider} / ${chatModel.label}`
                        : t.agentsPage.notAssigned
                      : t.agentsSettings.providerEnv.needsSetup
                  }
                />
                <StatusLine
                  label={t.agentsPage.chatModelReady}
                  ready={providerSetupComplete && (chatModel?.ready ?? false)}
                  detail={providerSetupComplete ? chatModel?.reason ?? t.agentsPage.notAssigned : t.agentsSettings.providerEnv.description}
                />
                <StatusLine
                  label={t.agentsPage.allowOverride}
                  ready
                  detail={draft?.allowChatOverride ? t.agentsPage.flexibleOverride : t.agentsPage.lockedOverride}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="agent-test-prompt">{t.agentsPage.testPrompt}</Label>
                <Textarea
                  id="agent-test-prompt"
                  value={testPrompt}
                  onChange={(event) => setTestPrompt(event.target.value)}
                  className="min-h-28"
                />
                <label className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    checked={useRetrieval}
                    onChange={(event) => setUseRetrieval(event.target.checked)}
                  />
                  {t.agentsPage.retrievalEnabled}
                </label>
                <Button
                  onClick={() => testMutation.mutate()}
                  disabled={testMutation.isPending || !providerSetupComplete || !chatModel}
                >
                  <Play className="h-4 w-4" />
                  {t.agentsPage.testAgent}
                </Button>
              </div>
              {testResult && (
                <div className="space-y-3 rounded-2xl border border-border/70 bg-background/80 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{t.agentsPage.lastResult}</div>
                    <Badge variant={testResult.status === "completed" ? "success" : "warning"}>
                      {testResult.status}
                    </Badge>
                  </div>
                  {testResult.reply && (
                    <div className="rounded-2xl border border-border/70 bg-muted/20 p-3 text-sm leading-6">
                      {testResult.reply}
                    </div>
                  )}
                  <div className="space-y-2 text-sm">
                    <div className="font-medium">{t.agentsPage.toolUsage}</div>
                    {testResult.tool_calls.length === 0 ? (
                      <div className="text-muted-foreground">{t.agentsPage.noToolUsage}</div>
                    ) : (
                      testResult.tool_calls.map((tool) => (
                        <div
                          key={`${tool.tool_name}-${tool.trace_id}`}
                          className="flex items-center justify-between rounded-xl border border-border/60 px-3 py-2"
                        >
                          <div>
                            <div className="font-medium">{tool.tool_name}</div>
                            <div className="text-xs text-muted-foreground">
                              {tool.latency_ms}ms
                            </div>
                          </div>
                          <Badge variant={tool.status === "success" ? "success" : "warning"}>
                            {tool.status}
                          </Badge>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link href={`/tasks/${testResult.task_id}`} className="text-sm font-medium text-primary hover:underline">
                      {t.agentsPage.openRunDetails}
                    </Link>
                    <Link href="/tasks" className="text-sm text-muted-foreground hover:text-foreground">
                      {t.agentsPage.viewAllRuns}
                    </Link>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card variant="surface">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">{t.agentsPage.recentContextTitle}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {selectedProfile ? (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">{t.agentsPage.updated}</span>
                  <span>{formatDateTime(selectedProfile.updated_at)}</span>
                </div>
              ) : (
                <div className="text-muted-foreground">{t.agentsPage.unsavedDraft}</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function RoutingCard({
  task,
  models,
  value,
  setupRequired,
  onChange,
}: {
  task: TaskDefinition;
  models: ModelOption[];
  value: string;
  setupRequired: boolean;
  onChange: (value: string) => void;
}) {
  const { t } = useI18n();
  const selected = parseProviderModelValue(value);
  const selectedModel =
    models.find(
      (model) => model.provider === selected?.provider && model.model === selected?.model,
    ) ?? null;

  return (
    <Card className="border-border/70 shadow-none">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-sm">{task.label}</CardTitle>
            <CardDescription>{task.description}</CardDescription>
          </div>
          {selectedModel && (
            <Badge variant={readinessBadgeVariant(selectedModel.ready)}>
              {selectedModel.ready ? t.agentsSettings.taskRouting.ready : t.agentsSettings.taskRouting.blocked}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {setupRequired ? (
          <div className="rounded-2xl border border-dashed border-border/70 bg-muted/20 p-3 text-xs text-muted-foreground">
            {t.agentsSettings.providerEnv.description}
          </div>
        ) : (
          <Select value={value} onValueChange={onChange}>
            <SelectTrigger>
              <SelectValue placeholder={t.common.selectModel} />
            </SelectTrigger>
            <SelectContent>
              {models.map((model) => (
                <SelectItem
                  key={composeProviderModel(model.provider, model.model)}
                  value={composeProviderModel(model.provider, model.model)}
                >
                  {model.label} / {model.provider}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {selectedModel && (
          <div className="rounded-2xl border border-border/70 bg-muted/20 p-3 text-xs text-muted-foreground">
            {selectedModel.reason}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PreviewPanel({
  draft,
  chatModel,
  selectedProfile,
}: {
  draft: ProfileDraft;
  chatModel: ModelOption | null;
  selectedProfile: AgentProfileResponse | null;
}) {
  const { t } = useI18n();

  return (
    <Card className="border-border/70 shadow-none">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">{t.agentsPage.previewTitle}</CardTitle>
        <CardDescription>{t.agentsPage.previewDescription}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            {t.agentsPage.tabIdentity}
          </div>
          <div className="mt-1 font-medium">{draft.name}</div>
          <div className="mt-1 text-muted-foreground">
            {draft.description || t.agentsPage.noDescription}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            {t.agentsPage.tabBehavior}
          </div>
          <div className="mt-2 rounded-2xl border border-border/70 bg-muted/20 p-3 text-muted-foreground">
            {draft.systemPrompt ? draft.systemPrompt.slice(0, 280) : t.agentsPage.needsSetup}
            {draft.systemPrompt.length > 280 ? "..." : ""}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
            {t.agentsPage.tabPreview}
          </div>
          <div className="mt-2 grid gap-2">
            <StatusLine
              label={t.agentsPage.chatRouting}
              ready={Boolean(chatModel)}
              detail={chatModel ? `${chatModel.provider} / ${chatModel.label}` : t.agentsPage.notAssigned}
            />
            <StatusLine
              label={t.agentsPage.allowOverride}
              ready
              detail={draft.allowChatOverride ? t.agentsPage.flexibleOverride : t.agentsPage.lockedOverride}
            />
            <StatusLine
              label={t.agentsPage.recentContextTitle}
              ready
              detail={
                selectedProfile
                  ? `${t.agentsPage.updated}: ${formatDateTime(selectedProfile.updated_at)}`
                  : t.agentsPage.unsavedDraft
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusLine({
  label,
  ready,
  detail,
}: {
  label: string;
  ready: boolean;
  detail?: string;
}) {
  const { t } = useI18n();

  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-border/60 px-3 py-2">
      <div>
        <div className="font-medium">{label}</div>
        {detail && <div className="text-xs text-muted-foreground">{detail}</div>}
      </div>
      <Badge variant={ready ? "success" : "warning"} className="shrink-0">
        {ready ? (
          <span className="inline-flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {t.agentsPage.runtimeCheckReady}
          </span>
        ) : (
          t.agentsPage.needsWork
        )}
      </Badge>
    </div>
  );
}
