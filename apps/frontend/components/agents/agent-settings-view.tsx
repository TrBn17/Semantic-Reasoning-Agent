"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, CircleAlert, Save, Shield, Sparkles } from "lucide-react";
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
  AgentProfileResponse,
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

interface ProviderDraft {
  enabled: boolean;
  values: Record<string, string>;
}

function composeValue(provider: string, model: string) {
  return `${provider}::${model}`;
}

function statusVariant(ready: boolean): "success" | "warning" {
  return ready ? "success" : "warning";
}

export function AgentSettingsView() {
  const queryClient = useQueryClient();
  const { workspaceId, preferredAgentProfileId, setPreferredAgentProfileId } = useWorkspaceStore();
  const { data, isLoading } = useQuery({
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

  useEffect(() => {
    if (!data) return;
    const nextProviderDrafts: Record<string, ProviderDraft> = {};
    for (const provider of data.providers) {
      const fieldByKey = Object.fromEntries(provider.fields.map((field) => [field.key, field]));
      nextProviderDrafts[provider.provider] = {
        enabled: provider.enabled,
        values: Object.fromEntries(
          provider.values.map((value) => [
            value.key,
            value.source === "database" && !fieldByKey[value.key]?.secret
              ? value.masked_value
              : "",
          ]),
        ),
      };
    }
    const nextTaskDrafts: Record<string, string> = {};
    for (const task of data.task_assignments) {
      nextTaskDrafts[task.task_type] = composeValue(task.provider, task.model);
    }
    setProviderDrafts(nextProviderDrafts);
    setTaskDrafts(nextTaskDrafts);
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
        selected.task_models.map((item) => [item.task_type, composeValue(item.provider, item.model)]),
      ),
    );
  }, [preferredAgentProfileId, profiles, selectedProfileId, setPreferredAgentProfileId]);

  const modelLookup = useMemo(() => {
    const source = data?.models ?? [];
    return Object.fromEntries(
      source.map((item) => [composeValue(item.provider, item.model), item]),
    );
  }, [data]);

  const mutation = useMutation({
    mutationFn: (payload: {
      providers: ProviderConfigUpdate[];
      task_assignments: TaskAssignmentUpdate[];
    }) =>
      updateAgentSettings({
        workspace_id: data?.workspace_id ?? workspaceId ?? "workspace-demo",
        ...payload,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.agents.settings(workspaceId), updated);
      queryClient.setQueryData([...queryKeys.models, workspaceId ?? null], updated.models);
      toast.success("Agent settings saved.");
    },
    onError: (err) => toast.error(`Save failed: ${(err as Error).message}`),
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
      toast.success("Agent profile created.");
    },
    onError: (err) => toast.error(`Create failed: ${(err as Error).message}`),
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
      toast.success("Profile saved.");
    },
    onError: (err) => toast.error(`Profile save failed: ${(err as Error).message}`),
  });

  const setDefaultMutation = useMutation({
    mutationFn: (profileId: string) => setDefaultAgentProfile(profileId),
    onSuccess: (profile) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      setPreferredAgentProfileId(profile.id);
      toast.success("Default profile updated.");
    },
    onError: (err) => toast.error(`Default update failed: ${(err as Error).message}`),
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div className="space-y-1.5">
            <CardTitle>Agent Builder Settings</CardTitle>
            <CardDescription>
              Người dùng có thể nhập env cho provider, xem model catalog và gán
              model theo từng tác vụ.
            </CardDescription>
          </div>
          <Button
            onClick={() =>
              mutation.mutate({
                providers: data.providers.map((provider) => ({
                  provider: provider.provider,
                  enabled: providerDrafts[provider.provider]?.enabled ?? provider.enabled,
                  values: providerDrafts[provider.provider]?.values ?? {},
                })),
                task_assignments: data.tasks
                  .map((task) => {
                    const value = taskDrafts[task.task_type];
                    if (!value) return null;
                    const [provider, model] = value.split("::");
                    if (!provider || !model) return null;
                    return { task_type: task.task_type, provider, model };
                  })
                  .filter(Boolean) as TaskAssignmentUpdate[],
              })
            }
            disabled={mutation.isPending}
          >
            <Save className="h-4 w-4" />
            Save Settings
          </Button>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border bg-muted/20 p-4">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Workspace
            </div>
            <div className="mt-2 font-medium">{data.workspace_id}</div>
          </div>
          <div className="rounded-lg border bg-muted/20 p-4">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Models
            </div>
            <div className="mt-2 font-medium">{data.models.length}</div>
          </div>
          <div className="rounded-lg border bg-muted/20 p-4">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Tasks
            </div>
            <div className="mt-2 font-medium">{data.tasks.length}</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Provider Env</CardTitle>
          <CardDescription>
            Cấu hình credential hoặc endpoint cho từng provider. `runtime`
            nghĩa là backend đang có env hệ thống, `database` là giá trị lưu từ UI.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.providers.map((provider) => {
            const draft = providerDrafts[provider.provider];
            return (
              <div
                key={provider.provider}
                className="rounded-xl border p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{provider.label}</h3>
                      <Badge variant={statusVariant(provider.ready)}>
                        {provider.ready ? "Ready" : "Needs setup"}
                      </Badge>
                      {!provider.supports_runtime && (
                        <Badge variant="outline">No runtime adapter</Badge>
                      )}
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {provider.reason}
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
                    {(draft?.enabled ?? provider.enabled) ? "Enabled" : "Disabled"}
                  </Button>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {provider.fields.length === 0 && (
                    <div className="text-sm text-muted-foreground">
                      Provider này không cần env bổ sung.
                    </div>
                  )}
                  {provider.fields.map((field) => {
                    const valueState = provider.values.find((item) => item.key === field.key);
                    const currentValue = draft?.values[field.key] ?? "";
                    return (
                      <div key={field.key} className="space-y-2">
                        <div className="flex items-center justify-between gap-3">
                          <Label htmlFor={`${provider.provider}-${field.key}`}>
                            {field.label}
                          </Label>
                          <Badge variant="outline">
                            {valueState?.source ?? "missing"}
                          </Badge>
                        </div>
                        <Input
                          id={`${provider.provider}-${field.key}`}
                          type={field.secret ? "password" : "text"}
                          value={currentValue}
                          placeholder={currentValue ? field.placeholder : valueState?.masked_value || field.placeholder}
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
                        <p className="text-xs text-muted-foreground">
                          {field.help_text}
                          {valueState?.configured ? ` Current: ${valueState.masked_value}` : ""}
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
          <CardTitle>Agent Profiles</CardTitle>
          <CardDescription>
            Hồ sơ agent có prompt riêng, task routing riêng và policy cho phép override model trong chat.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Input
              value={newProfileName}
              onChange={(event) => setNewProfileName(event.target.value)}
              placeholder="New profile name"
              className="max-w-sm"
            />
            <Button
              onClick={() => createProfileMutation.mutate()}
              disabled={createProfileMutation.isPending || !newProfileName.trim()}
            >
              <Sparkles className="h-4 w-4" />
              Create Profile
            </Button>
          </div>

          <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
            <div className="space-y-3">
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
                          composeValue(item.provider, item.model),
                        ]),
                      ),
                    );
                  }}
                  className="w-full rounded-xl border p-4 text-left"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{profile.name}</span>
                    {profile.is_default && <Badge variant="success">Default</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{profile.description || "No description"}</p>
                </button>
              ))}
            </div>

            {(() => {
              const selectedProfile = (profiles ?? []).find((item) => item.id === selectedProfileId);
              if (!selectedProfile) {
                return <div className="rounded-xl border p-4 text-sm text-muted-foreground">No profile selected.</div>;
              }
              return (
                <div className="space-y-4 rounded-xl border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{selectedProfile.name}</h3>
                      <p className="text-sm text-muted-foreground">Profile-bound prompt, routing and override policy.</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => setDefaultMutation.mutate(selectedProfile.id)}
                        disabled={setDefaultMutation.isPending || selectedProfile.is_default}
                      >
                        <Shield className="h-4 w-4" />
                        Set Default
                      </Button>
                      <Button
                        onClick={() => saveProfileMutation.mutate(selectedProfile)}
                        disabled={saveProfileMutation.isPending}
                      >
                        <Save className="h-4 w-4" />
                        Save Profile
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile-description">Description</Label>
                    <Input
                      id="profile-description"
                      value={profileDescriptionDraft}
                      onChange={(event) => setProfileDescriptionDraft(event.target.value)}
                      placeholder="What this agent is for"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="profile-prompt">System Prompt</Label>
                    <Textarea
                      id="profile-prompt"
                      value={profilePromptDraft}
                      onChange={(event) => setProfilePromptDraft(event.target.value)}
                      placeholder="You are an analyst agent..."
                      className="min-h-[140px]"
                    />
                  </div>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={profileAllowOverrideDraft}
                      onChange={(event) => setProfileAllowOverrideDraft(event.target.checked)}
                    />
                    Allow chat model override
                  </label>
                  <div className="space-y-3">
                    {data.tasks.map((task) => (
                      <div key={task.task_type} className="grid gap-2 md:grid-cols-[200px_1fr] md:items-center">
                        <div>
                          <div className="font-medium">{task.label}</div>
                          <div className="text-xs text-muted-foreground">{task.description}</div>
                        </div>
                        <Select
                          value={profileTaskDrafts[task.task_type]}
                          onValueChange={(value) =>
                            setProfileTaskDrafts((current) => ({ ...current, [task.task_type]: value }))
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select model" />
                          </SelectTrigger>
                          <SelectContent>
                            {data.models.map((model) => (
                              <SelectItem
                                key={`${task.task_type}-${composeValue(model.provider, model.model)}`}
                                value={composeValue(model.provider, model.model)}
                              >
                                {model.label} · {model.provider}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Task Routing</CardTitle>
          <CardDescription>
            Chọn model mặc định cho từng tác vụ. Đây là lớp cấu hình đầu tiên để
            tiến tới agent builder theo profile.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.tasks.map((task) => {
            const selectedValue = taskDrafts[task.task_type];
            const selectedModel = selectedValue ? modelLookup[selectedValue] : null;
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
                    <Badge variant={statusVariant(selectedModel.ready)}>
                      {selectedModel.ready ? "Ready" : "Blocked"}
                    </Badge>
                  )}
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-[minmax(0,320px)_1fr]">
                  <Select
                    value={selectedValue}
                    onValueChange={(value) =>
                      setTaskDrafts((current) => ({ ...current, [task.task_type]: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      {data.models.map((model) => (
                        <SelectItem
                          key={composeValue(model.provider, model.model)}
                          value={composeValue(model.provider, model.model)}
                        >
                          {model.label} · {model.provider}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <div className="rounded-lg bg-muted/20 p-4 text-sm">
                    {selectedModel ? (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          {selectedModel.ready ? (
                            <Check className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <CircleAlert className="h-4 w-4 text-amber-600" />
                          )}
                          <span className="font-medium">
                            {selectedModel.label} ({selectedModel.provider})
                          </span>
                        </div>
                        <p className="text-muted-foreground">
                          {selectedModel.description}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">
                            Context {selectedModel.context_window?.toLocaleString() ?? "n/a"}
                          </Badge>
                          <Badge variant="outline">
                            {selectedModel.supports_structured_output
                              ? "Structured output"
                              : "No structured output"}
                          </Badge>
                          <Badge variant="outline">
                            {selectedModel.supports_streaming ? "Streaming" : "No streaming"}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {selectedModel.reason}
                        </p>
                      </div>
                    ) : (
                      <p className="text-muted-foreground">
                        Chưa chọn model cho tác vụ này.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model Catalog</CardTitle>
          <CardDescription>
            Metadata của model để người dùng biết model nào hợp chat,
            extraction, narrative hay dashboard.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-2">
          {data.models.map((model) => (
            <div key={composeValue(model.provider, model.model)} className="rounded-xl border p-4">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold">{model.label}</h3>
                <Badge variant={statusVariant(model.ready)}>
                  {model.ready ? "Ready" : "Blocked"}
                </Badge>
                {!model.supports_runtime && <Badge variant="outline">Missing adapter</Badge>}
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{model.description}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge variant="outline">{model.provider}</Badge>
                <Badge variant="outline">{model.model}</Badge>
                <Badge variant="outline">
                  Context {model.context_window?.toLocaleString() ?? "n/a"}
                </Badge>
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                Recommended for: {model.recommended_for.join(", ") || "n/a"}
              </div>
              <div className="mt-2 text-xs text-muted-foreground">{model.reason}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
