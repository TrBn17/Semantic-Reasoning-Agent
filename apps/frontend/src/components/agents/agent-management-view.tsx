"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save, Shield } from "lucide-react";
import {
  formatPresetLabel,
  summarizeKnowledgeScope,
} from "@/components/agents/model-picker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ModelCombobox } from "@/components/agents/model-combobox";
import { ToolSlotBoard } from "@/components/agents/tool-slot-board";
import { getCapabilityCatalog } from "@/shared/api/agent-capabilities";
import {
  listAgentProfiles,
  setDefaultAgentProfile,
  updateAgentProfile,
} from "@/shared/api/agent-profiles";
import { listDocuments } from "@/shared/api/documents";
import { createKnowledgePack, listKnowledgePacks, updateKnowledgePack } from "@/shared/api/knowledge-packs";
import { listSearchTools } from "@/shared/api/search-tools";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useSettingsModelsQuery } from "@/shared/hooks/use-settings-models-query";
import type { Dictionary } from "@/shared/i18n/dictionaries";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { notify } from "@/shared/ui/notify";
import { composeModelValue, parseModelValue } from "@/shared/utils/model-value";
import type {
  AgentProfileResponse,
  EvidencePolicySchema,
  KnowledgePackResponse,
  ToolPolicySchema,
  AgentProfileToolAssignment,
  OrchestrationMode,
  LlmInferenceOverrides,
} from "@/shared/api/types";

type ProfileDraft = {
  profileName: string;
  description: string;
  systemPrompt: string;
  llmProvider: string;
  llmModel: string;
  llmTemperature: string;
  llmMaxTokens: string;
  llmReasoningEffort: string;
  capabilityPreset: string;
  toolPolicyMode: string;
  allowedTools: string[];
  blockedTools: string[];
  toolAssignments: AgentProfileToolAssignment[];
  knowledgePackIds: string[];
  allowedSources: string[];
  allowModelOnlyFallback: boolean;
  orchestrationMode: OrchestrationMode;
  orchestrationEnabled: boolean;
  orchestrationMaxIterations: number;
};

type KnowledgePackDraft = {
  name: string;
  description: string;
  status: string;
  documentIds: string[];
};

const DEFAULT_ALLOWED_SOURCES = [
  "internal_chunk",
  "graph_node",
  "graph_edge",
  "web_page",
  "mcp_result",
  "generated_artifact",
];

function makeProfileDraft(profile: AgentProfileResponse): ProfileDraft {
  const inf = profile.llm_inference;
  return {
    profileName: profile.name,
    description: profile.description,
    systemPrompt: profile.system_prompt,
    llmProvider: inf?.provider?.trim() ?? "",
    llmModel: inf?.model?.trim() ?? "",
    llmTemperature: inf?.temperature != null && !Number.isNaN(inf.temperature) ? String(inf.temperature) : "",
    llmMaxTokens: inf?.max_tokens != null && !Number.isNaN(inf.max_tokens) ? String(inf.max_tokens) : "",
    llmReasoningEffort: inf?.reasoning_effort ?? "none",
    capabilityPreset: profile.capability_preset,
    toolPolicyMode: profile.tool_policy.mode,
    allowedTools: [...profile.tool_policy.allowed_tools],
    blockedTools: [...profile.tool_policy.blocked_tools],
    toolAssignments: [...profile.tool_assignments],
    knowledgePackIds: [...profile.knowledge_pack_ids],
    allowedSources: [...profile.evidence_policy.allowed_sources],
    allowModelOnlyFallback: profile.evidence_policy.allow_model_only_fallback,
    orchestrationMode: profile.orchestration_config.mode,
    orchestrationEnabled: profile.orchestration_config.orchestrator.enabled,
    orchestrationMaxIterations: profile.orchestration_config.stop_policy.max_iterations,
  };
}

function makeKnowledgePackDraft(pack?: KnowledgePackResponse | null): KnowledgePackDraft {
  return {
    name: pack?.name ?? "",
    description: pack?.description ?? "",
    status: pack?.status ?? "active",
    documentIds: [...(pack?.document_ids ?? [])],
  };
}

function hydrateProfileDraft(
  profile: AgentProfileResponse,
  defaultToolAssignments: AgentProfileToolAssignment[],
): ProfileDraft {
  const nextDraft = makeProfileDraft(profile);
  if (nextDraft.toolAssignments.length === 0 && defaultToolAssignments.length > 0) {
    nextDraft.toolAssignments = defaultToolAssignments;
  }
  return nextDraft;
}

function buildToolPolicy(draft: ProfileDraft): ToolPolicySchema {
  return {
    mode: draft.toolPolicyMode,
    allowed_tools: [...draft.allowedTools],
    blocked_tools: [...draft.blockedTools],
  };
}

function buildEvidencePolicy(draft: ProfileDraft): EvidencePolicySchema {
  return {
    allowed_sources: draft.allowedSources,
    allow_model_only_fallback: draft.allowModelOnlyFallback,
  };
}

function buildLlmInferencePayload(draft: ProfileDraft): LlmInferenceOverrides | null {
  const hasAny =
    draft.llmProvider.trim() ||
    draft.llmModel.trim() ||
    draft.llmTemperature.trim() ||
    draft.llmMaxTokens.trim() ||
    (draft.llmReasoningEffort && draft.llmReasoningEffort !== "none");
  if (!hasAny) {
    return null;
  }
  const temp = draft.llmTemperature.trim() ? Number(draft.llmTemperature) : null;
  const maxTok = draft.llmMaxTokens.trim() ? Number(draft.llmMaxTokens) : null;
  return {
    provider: draft.llmProvider.trim() || null,
    model: draft.llmModel.trim() || null,
    temperature: temp != null && !Number.isNaN(temp) ? temp : null,
    max_tokens: maxTok != null && !Number.isNaN(maxTok) ? maxTok : null,
    reasoning_effort:
      draft.llmReasoningEffort === "none" || !draft.llmReasoningEffort
        ? null
        : (draft.llmReasoningEffort as LlmInferenceOverrides["reasoning_effort"]),
  };
}

function inferenceComboFromDraft(provider: string, model: string): string {
  const p = provider.trim();
  const m = model.trim();
  if (!p || !m) return "";
  return composeModelValue(p, m);
}

function builtinRoleSubtitle(
  profile: AgentProfileResponse,
  agentManagement: Dictionary["agentManagement"],
): string | null {
  if (!profile.builtin_agent_role) return null;
  switch (profile.builtin_agent_role) {
    case "orchestrator":
      return agentManagement.builtinRoleOrchestrator;
    case "graph":
      return agentManagement.builtinRoleGraph;
    case "docs":
      return agentManagement.builtinRoleDocs;
    default:
      return profile.builtin_agent_role;
  }
}

export function AgentManagementView() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useActiveWorkspaceId();
  const preferredAgentProfileId = useWorkspaceStore((state) => state.preferredAgentProfileId);
  const setPreferredAgentProfileId = useWorkspaceStore((state) => state.setPreferredAgentProfileId);
  const { data: profiles, isLoading } = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });
  const { data: capabilityCatalog } = useQuery({
    queryKey: queryKeys.capabilities.catalog(),
    queryFn: getCapabilityCatalog,
  });
  const { data: searchTools = [] } = useQuery({
    queryKey: queryKeys.searchTools.list(workspaceId),
    queryFn: () => listSearchTools({ workspaceId: workspaceId ?? undefined }),
  });
  const { data: knowledgePacks = [] } = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
  });
  const { data: documents = [] } = useQuery({
    queryKey: ["documents", "list", workspaceId ?? null],
    queryFn: () => listDocuments(workspaceId),
  });
  const { data: settingsModels = [] } = useSettingsModelsQuery();
  const sortedSettingsModels = useMemo(
    () =>
      [...settingsModels].sort((a, b) => {
        if (a.ready !== b.ready) return a.ready ? -1 : 1;
        return a.label.localeCompare(b.label);
      }),
    [settingsModels],
  );

  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft | null>(null);
  const [knowledgeDialogOpen, setKnowledgeDialogOpen] = useState(false);
  const [editingPack, setEditingPack] = useState<KnowledgePackResponse | null>(null);
  const [knowledgePackDraft, setKnowledgePackDraft] = useState<KnowledgePackDraft>(makeKnowledgePackDraft());

  const selectedProfile = useMemo(
    () => profiles?.find((item) => item.id === selectedProfileId) ?? null,
    [profiles, selectedProfileId],
  );
  const canSetWorkspaceDefault = useMemo(() => {
    if (!selectedProfile) return false;
    const role = selectedProfile.builtin_agent_role;
    return !role || role === "orchestrator";
  }, [selectedProfile]);
  const selectedPreset = useMemo(
    () => capabilityCatalog?.presets.find((item) => item.preset === profileDraft?.capabilityPreset) ?? null,
    [capabilityCatalog?.presets, profileDraft?.capabilityPreset],
  );
  const builtinRole = selectedProfile?.builtin_agent_role ?? null;
  const defaultToolAssignments = useMemo(
    () =>
      searchTools
        .filter((tool) => tool.is_system)
        .flatMap((tool) =>
          tool.assignable_slots.slice(0, 1).map((slot, index) => ({
            slot,
            tool_name: tool.tool_name,
            config_id: tool.id,
            enabled: true,
            position: slot === "rag" ? 0 : 1 + index,
          })),
        ),
    [searchTools],
  );
  useEffect(() => {
    const selected =
      profiles?.find((item) => item.id === selectedProfileId) ??
      profiles?.find((item) => item.id === preferredAgentProfileId) ??
      profiles?.find((item) => item.is_default) ??
      profiles?.[0];
    if (!selected) return;
    setSelectedProfileId((current) => (current === selected.id ? current : selected.id));
    if (preferredAgentProfileId !== selected.id) {
      setPreferredAgentProfileId(selected.id);
    }
    setProfileDraft((current) => {
      if (current && selectedProfileId === selected.id) {
        return current;
      }
      return hydrateProfileDraft(selected, defaultToolAssignments);
    });
  }, [defaultToolAssignments, preferredAgentProfileId, profiles, selectedProfileId, setPreferredAgentProfileId]);
  const saveProfileMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile || !profileDraft) {
        throw new Error("Select a profile first.");
      }
      return updateAgentProfile(selectedProfile.id, {
        name: profileDraft.profileName.trim(),
        description: profileDraft.description,
        system_prompt: profileDraft.systemPrompt,
        allow_chat_model_override: true,
        capability_preset: profileDraft.capabilityPreset,
        tool_policy: buildToolPolicy(profileDraft),
        tool_assignments: profileDraft.toolAssignments,
        knowledge_pack_ids: profileDraft.knowledgePackIds,
        evidence_policy: buildEvidencePolicy(profileDraft),
        orchestration_config: {
          version: "1.0",
          mode: profileDraft.orchestrationMode,
          orchestrator: {
            strategy: profileDraft.orchestrationMode,
            enabled: profileDraft.orchestrationEnabled,
          },
          stop_policy: {
            max_iterations: profileDraft.orchestrationMaxIterations,
          },
        },
        llm_inference: buildLlmInferencePayload(profileDraft),
      });
    },
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      setProfileDraft(hydrateProfileDraft(updated, defaultToolAssignments));
      notify.success(t.agentsSettings.toasts.profileSaved);
    },
    onError: (error) => notify.error(`${t.agentsSettings.toasts.profileSaveFailedPrefix} ${(error as Error).message}`, t.common.error),
  });

  const setDefaultMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile) throw new Error("Select a profile first.");
      return setDefaultAgentProfile(selectedProfile.id);
    },
    onSuccess: async (profile) => {
      setPreferredAgentProfileId(profile.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      notify.success(t.agentsSettings.toasts.defaultProfileUpdated);
    },
    onError: (error) => notify.error(`${t.agentsSettings.toasts.defaultUpdateFailedPrefix} ${(error as Error).message}`, t.common.error),
  });

  const saveKnowledgePackMutation = useMutation({
    mutationFn: () => {
      if (editingPack) {
        return updateKnowledgePack(editingPack.id, {
          name: knowledgePackDraft.name.trim(),
          description: knowledgePackDraft.description,
          status: knowledgePackDraft.status,
          document_ids: knowledgePackDraft.documentIds,
        });
      }
      if (!workspaceId) {
        throw new Error("Workspace is not resolved.");
      }
      return createKnowledgePack({
        workspace_id: workspaceId,
        name: knowledgePackDraft.name.trim(),
        description: knowledgePackDraft.description,
        status: knowledgePackDraft.status,
        document_ids: knowledgePackDraft.documentIds,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.knowledgePacks.list(workspaceId) });
      setKnowledgeDialogOpen(false);
      setEditingPack(null);
      setKnowledgePackDraft(makeKnowledgePackDraft());
      notify.success(t.agentManagement.toastKnowledgePackSaved);
    },
    onError: (error) =>
      notify.error(`${t.agentManagement.toastKnowledgePackSaveFailedPrefix} ${(error as Error).message}`, t.common.error),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-24">
      <Card>
        <CardHeader>
          <CardTitle>{t.agentManagement.title}</CardTitle>
          <CardDescription>{t.agentManagement.description}</CardDescription>
        </CardHeader>
      </Card>

      <div className="grid items-start gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>{t.agentManagement.profilesTitle}</CardTitle>
            <CardDescription>{t.agentManagement.profilesDescription}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {(profiles ?? []).map((profile) => {
                const roleSubtitle = builtinRoleSubtitle(profile, t.agentManagement);
                return (
                  <button
                    key={profile.id}
                    type="button"
                    onClick={() => {
                      setSelectedProfileId(profile.id);
                      setPreferredAgentProfileId(profile.id);
                      setProfileDraft(hydrateProfileDraft(profile, defaultToolAssignments));
                    }}
                    className={`w-full rounded-2xl border p-4 text-left transition ${
                      selectedProfileId === profile.id
                        ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                        : "hover:border-primary/40"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{profile.name}</span>
                      {profile.builtin_agent_role ? (
                        <Badge variant="secondary">{t.agentManagement.builtinBadge}</Badge>
                      ) : null}
                      {profile.is_default && <Badge variant="success">{t.agentManagement.defaultBadge}</Badge>}
                    </div>
                    {roleSubtitle ? (
                      <p className="mt-1 text-xs text-muted-foreground">{roleSubtitle}</p>
                    ) : null}
                    <p className="mt-1 text-sm text-muted-foreground">
                      {profile.description || t.agentManagement.noDescription}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>{formatPresetLabel(profile.capability_preset)}</span>
                      <span>{summarizeKnowledgeScope(profile.knowledge_pack_ids.length)}</span>
                    </div>
                  </button>
                );
              })}
              {(profiles ?? []).length === 0 && (
                <div className="rounded-2xl border border-dashed p-6 text-sm text-muted-foreground">
                  {t.agentManagement.noProfiles}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {!selectedProfile || !profileDraft ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">{t.agentManagement.selectProfileHint}</CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>
                  {builtinRole ? t.agentManagement.runtimeConfigTitle : t.agentManagement.identityTitle}
                </CardTitle>
                <CardDescription>
                  {builtinRole === "orchestrator"
                    ? t.agentManagement.runtimeOrchestratorHint
                    : builtinRole === "graph"
                      ? t.agentManagement.runtimeGraphHint
                      : builtinRole === "docs"
                        ? t.agentManagement.runtimeDocsHint
                        : t.agentManagement.identityDescription}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{t.agentManagement.name}</Label>
                    <Input
                      value={profileDraft.profileName}
                      onChange={(event) =>
                        setProfileDraft((current) =>
                          current ? { ...current, profileName: event.target.value } : current,
                        )
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.status}</Label>
                    <Input value={selectedProfile.status} disabled />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t.agentManagement.descriptionLabel}</Label>
                  <Input
                    value={profileDraft.description}
                    onChange={(event) =>
                      setProfileDraft((current) => (current ? { ...current, description: event.target.value } : current))
                    }
                    placeholder={t.agentManagement.descriptionPlaceholder}
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-2 md:col-span-2 lg:col-span-3">
                  <div className="flex flex-wrap items-end justify-between gap-2">
                    <div>
                      <Label>{t.agentManagement.inferenceModelLabel}</Label>
                      <p className="mt-1 text-xs text-muted-foreground">{t.agentManagement.inferenceModelHint}</p>
                    </div>
                    {inferenceComboFromDraft(profileDraft.llmProvider, profileDraft.llmModel) ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="shrink-0 text-xs"
                        onClick={() =>
                          setProfileDraft((current) =>
                            current ? { ...current, llmProvider: "", llmModel: "" } : current,
                          )
                        }
                      >
                        {t.agentManagement.inferenceModelClear}
                      </Button>
                    ) : null}
                  </div>
                  <ModelCombobox
                    models={sortedSettingsModels}
                    value={inferenceComboFromDraft(profileDraft.llmProvider, profileDraft.llmModel)}
                    onChange={(value) => {
                      const parsed = parseModelValue(value);
                      setProfileDraft((current) =>
                        current
                          ? {
                              ...current,
                              llmProvider: parsed?.provider ?? "",
                              llmModel: parsed?.model ?? "",
                            }
                          : current,
                      );
                    }}
                    collapseOnSelect
                    labels={{
                      providerPlaceholder: t.agentsSettings.picker.providerPlaceholder,
                      allProviders: t.agentsSettings.picker.allProviders,
                      searchModelPlaceholder: t.chatRuntimeControls.searchProviderModel,
                      selectModelPlaceholder: t.chatRuntimeControls.selectModel,
                      noModelMatch: t.agentsSettings.picker.noModelMatch,
                      assignmentUnavailable: t.agentsSettings.picker.assignmentUnavailable,
                      typePlaceholder: t.agentsSettings.picker.typePlaceholder,
                      allTypes: t.agentsSettings.picker.allTypes,
                      readyBadge: t.agentsSettings.taskRouting.ready,
                      blockedBadge: t.agentsSettings.taskRouting.blocked,
                      capabilityStreaming: t.agentsSettings.taskRouting.streaming,
                      capabilityStructured: t.agentsSettings.taskRouting.structuredOutput,
                    }}
                  />
                </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.temperatureLabel}</Label>
                    <Input
                      type="number"
                      step="0.1"
                      min={0}
                      max={2}
                      value={profileDraft.llmTemperature}
                      onChange={(event) =>
                        setProfileDraft((current) =>
                          current ? { ...current, llmTemperature: event.target.value } : current,
                        )
                      }
                      placeholder="0.2"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.maxTokensLabel}</Label>
                    <Input
                      type="number"
                      min={1}
                      value={profileDraft.llmMaxTokens}
                      onChange={(event) =>
                        setProfileDraft((current) =>
                          current ? { ...current, llmMaxTokens: event.target.value } : current,
                        )
                      }
                      placeholder="4096"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.reasoningLabel}</Label>
                    <Select
                      value={profileDraft.llmReasoningEffort || "none"}
                      onValueChange={(value) =>
                        setProfileDraft((current) =>
                          current ? { ...current, llmReasoningEffort: value } : current,
                        )
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">{t.agentManagement.reasoningNone}</SelectItem>
                        <SelectItem value="low">{t.agentManagement.reasoningLow}</SelectItem>
                        <SelectItem value="medium">{t.agentManagement.reasoningMedium}</SelectItem>
                        <SelectItem value="high">{t.agentManagement.reasoningHigh}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>{t.agentManagement.systemPromptLabel}</Label>
                  <Textarea
                    value={profileDraft.systemPrompt}
                    onChange={(event) =>
                      setProfileDraft((current) => (current ? { ...current, systemPrompt: event.target.value } : current))
                    }
                    className="min-h-[160px]"
                    placeholder={t.agentManagement.systemPromptPlaceholder}
                  />
                </div>
              </CardContent>
            </Card>

            {builtinRole === "graph" ? (
              <Card>
                <CardHeader>
                  <CardTitle>{t.agentManagement.graphStoreTitle}</CardTitle>
                  <CardDescription>{t.agentManagement.graphStoreDescription}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ToolSlotBoard
                    tools={searchTools}
                    assignments={profileDraft.toolAssignments}
                    onChange={(toolAssignments) =>
                      setProfileDraft((current) => (current ? { ...current, toolAssignments } : current))
                    }
                    visibleSlots={["ontology_search"]}
                  />
                </CardContent>
              </Card>
            ) : null}

            {builtinRole === "docs" ? (
              <Card>
                <CardHeader>
                  <CardTitle>{t.agentManagement.vecStoreTitle}</CardTitle>
                  <CardDescription>{t.agentManagement.vecStoreDescription}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ToolSlotBoard
                    tools={searchTools}
                    assignments={profileDraft.toolAssignments}
                    onChange={(toolAssignments) =>
                      setProfileDraft((current) => (current ? { ...current, toolAssignments } : current))
                    }
                    visibleSlots={["rag"]}
                  />
                </CardContent>
              </Card>
            ) : null}

            {!builtinRole ? (
            <Card>
              <CardHeader>
                <CardTitle>{t.agentManagement.capabilityTitle}</CardTitle>
                <CardDescription>{t.agentManagement.capabilityDescription}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t.agentManagement.capabilityPreset}</Label>
                  <Select
                    value={profileDraft.capabilityPreset}
                    onValueChange={(value) =>
                      setProfileDraft((current) => (current ? { ...current, capabilityPreset: value } : current))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={t.agentManagement.selectPresetPlaceholder} />
                    </SelectTrigger>
                    <SelectContent>
                      {(capabilityCatalog?.presets ?? []).map((preset) => (
                        <SelectItem key={preset.preset} value={preset.preset}>
                          {preset.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {selectedPreset && (
                  <div className="rounded-2xl border p-4">
                    <h3 className="font-semibold">{selectedPreset.label}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{selectedPreset.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      {selectedPreset.allowed_tool_families.map((family) => (
                        <Badge key={family} variant="outline">
                          {family}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{t.agentManagement.toolPolicyMode}</Label>
                    <Select
                      value={profileDraft.toolPolicyMode}
                      onValueChange={(value) =>
                        setProfileDraft((current) => (current ? { ...current, toolPolicyMode: value } : current))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="preset">{t.agentManagement.policyPreset}</SelectItem>
                        <SelectItem value="allowlist">{t.agentManagement.policyAllowlist}</SelectItem>
                        <SelectItem value="blocklist">{t.agentManagement.policyBlocklist}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.presetSummary}</Label>
                    <Input
                      value={selectedPreset?.default_tool_order.join(", ") ?? t.agentManagement.noPresetSelected}
                      disabled
                    />
                  </div>
                </div>

                <ToolSlotBoard
                  tools={searchTools}
                  assignments={profileDraft.toolAssignments}
                  onChange={(toolAssignments) =>
                    setProfileDraft((current) => (current ? { ...current, toolAssignments } : current))
                  }
                />
              </CardContent>
            </Card>
            ) : null}

            {!builtinRole || builtinRole === "docs" ? (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{t.agentManagement.knowledgeTitle}</CardTitle>
                  <CardDescription>{t.agentManagement.knowledgeDescription}</CardDescription>
                </div>
                <Dialog
                  open={knowledgeDialogOpen}
                  onOpenChange={(open) => {
                    setKnowledgeDialogOpen(open);
                    if (!open) {
                      setEditingPack(null);
                      setKnowledgePackDraft(makeKnowledgePackDraft());
                    }
                  }}
                >
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditingPack(null);
                        setKnowledgePackDraft(makeKnowledgePackDraft());
                      }}
                    >
                      <Plus className="h-4 w-4" />
                      {t.agentManagement.newPack}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl" closeLabel={t.common.accessibility.closeDialog}>
                    <DialogHeader>
                      <DialogTitle>
                        {editingPack ? t.agentManagement.editKnowledgePack : t.agentManagement.createKnowledgePack}
                      </DialogTitle>
                      <DialogDescription>{t.agentManagement.knowledgeDialogDescription}</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label>{t.agentManagement.packName}</Label>
                          <Input
                            value={knowledgePackDraft.name}
                            onChange={(event) =>
                              setKnowledgePackDraft((current) => ({ ...current, name: event.target.value }))
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>{t.agentManagement.packStatus}</Label>
                          <Select
                            value={knowledgePackDraft.status}
                            onValueChange={(value) =>
                              setKnowledgePackDraft((current) => ({ ...current, status: value }))
                            }
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="active">{t.agentManagement.activeStatus}</SelectItem>
                              <SelectItem value="archived">{t.agentManagement.archivedStatus}</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>{t.agentManagement.packDescription}</Label>
                        <Textarea
                          value={knowledgePackDraft.description}
                          onChange={(event) =>
                            setKnowledgePackDraft((current) => ({ ...current, description: event.target.value }))
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>{t.agentManagement.packDocuments}</Label>
                        <ScrollArea className="h-64 rounded-xl border">
                          <div className="space-y-2 p-3">
                            {documents.map((document) => {
                              const checked = knowledgePackDraft.documentIds.includes(document.id);
                              return (
                                <label key={document.id} className="flex items-start gap-3 rounded-lg border p-3 text-sm">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(event) =>
                                      setKnowledgePackDraft((current) => ({
                                        ...current,
                                        documentIds: event.target.checked
                                          ? [...current.documentIds, document.id]
                                          : current.documentIds.filter((item) => item !== document.id),
                                      }))
                                    }
                                  />
                                  <div>
                                    <div className="font-medium">{document.title}</div>
                                    <div className="text-xs text-muted-foreground">{document.status}</div>
                                  </div>
                                </label>
                              );
                            })}
                          </div>
                        </ScrollArea>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setKnowledgeDialogOpen(false)}>
                        {t.agentManagement.cancel}
                      </Button>
                      <Button
                        onClick={() => saveKnowledgePackMutation.mutate()}
                        disabled={saveKnowledgePackMutation.isPending || !knowledgePackDraft.name.trim()}
                      >
                        {t.agentManagement.savePack}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 lg:grid-cols-2">
                  {knowledgePacks.map((pack) => {
                    const checked = profileDraft.knowledgePackIds.includes(pack.id);
                    return (
                      <div key={pack.id} className="rounded-2xl border p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold">{pack.name}</h3>
                              <Badge variant="outline">{pack.status}</Badge>
                            </div>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {pack.description || t.agentManagement.noDescription}
                            </p>
                            <p className="mt-2 text-xs text-muted-foreground">
                              {pack.document_ids.length} {t.agentManagement.linkedDocs}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingPack(pack);
                              setKnowledgePackDraft(makeKnowledgePackDraft(pack));
                              setKnowledgeDialogOpen(true);
                            }}
                          >
                            {t.agentManagement.edit}
                          </Button>
                        </div>
                        <label className="mt-4 flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(event) =>
                              setProfileDraft((current) =>
                                current
                                  ? {
                                      ...current,
                                      knowledgePackIds: event.target.checked
                                        ? [...current.knowledgePackIds, pack.id]
                                        : current.knowledgePackIds.filter((item) => item !== pack.id),
                                    }
                                  : current,
                              )
                            }
                          />
                          {t.agentManagement.attachProfile}
                        </label>
                        {checked && pack.document_ids.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            {pack.document_ids.slice(0, 4).map((documentId) => (
                              <Badge key={documentId} variant="outline">
                                {documents.find((item) => item.id === documentId)?.title ?? documentId}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {knowledgePacks.length === 0 && (
                  <div className="rounded-2xl border border-dashed p-6 text-sm text-muted-foreground">
                    {t.agentManagement.noPacks}
                  </div>
                )}
              </CardContent>
            </Card>
            ) : null}

            {!builtinRole ? (
            <Card>
              <CardHeader>
                <CardTitle>{t.agentManagement.evidenceTitle}</CardTitle>
                <CardDescription>{t.agentManagement.evidenceDescription}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {DEFAULT_ALLOWED_SOURCES.map((source) => (
                    <label key={source} className="flex items-center gap-2 rounded-xl border p-3 text-sm">
                      <input
                        type="checkbox"
                        checked={profileDraft.allowedSources.includes(source)}
                        onChange={(event) =>
                          setProfileDraft((current) =>
                            current
                              ? {
                                  ...current,
                                  allowedSources: event.target.checked
                                    ? [...current.allowedSources, source]
                                    : current.allowedSources.filter((item) => item !== source),
                                }
                              : current,
                          )
                        }
                      />
                      {source}
                    </label>
                  ))}
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={profileDraft.allowModelOnlyFallback}
                    onChange={(event) =>
                      setProfileDraft((current) =>
                        current
                          ? { ...current, allowModelOnlyFallback: event.target.checked }
                          : current,
                      )
                    }
                  />
                  {t.agentManagement.modelOnlyFallback}
                </label>
              </CardContent>
            </Card>
            ) : null}

            {!builtinRole || builtinRole === "orchestrator" ? (
            <Card>
              <CardHeader>
                <CardTitle>{t.agentManagement.orchestrationTitle}</CardTitle>
                <CardDescription>{t.agentManagement.orchestrationDescription}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{t.agentManagement.orchestrationModeLabel}</Label>
                    <Select
                      value={profileDraft.orchestrationMode}
                      onValueChange={(value) =>
                        setProfileDraft((current) =>
                          current
                            ? { ...current, orchestrationMode: value as OrchestrationMode }
                            : current,
                        )
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="legacy_static_plan">legacy_static_plan</SelectItem>
                        <SelectItem value="react_two_agent">react_two_agent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>{t.agentManagement.orchestrationMaxIterationsLabel}</Label>
                    <Input
                      type="number"
                      min={1}
                      max={12}
                      value={profileDraft.orchestrationMaxIterations}
                      onChange={(event) =>
                        setProfileDraft((current) =>
                          current
                            ? {
                                ...current,
                                orchestrationMaxIterations: Math.max(
                                  1,
                                  Math.min(12, Number(event.target.value || 1)),
                                ),
                              }
                            : current,
                        )
                      }
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={profileDraft.orchestrationEnabled}
                    onChange={(event) =>
                      setProfileDraft((current) =>
                        current ? { ...current, orchestrationEnabled: event.target.checked } : current,
                      )
                    }
                  />
                  {t.agentManagement.orchestrationEnabledLabel}
                </label>
                <div className="rounded-xl border p-3 text-xs text-muted-foreground">
                  {builtinRole === "orchestrator"
                    ? t.agentManagement.orchestrationBuiltinOrchestratorHint
                    : t.agentManagement.orchestrationReactHint}
                </div>
              </CardContent>
            </Card>
            ) : null}
          </div>
        )}
      </div>

      {selectedProfile && profileDraft && (
        <div className="fixed inset-x-0 bottom-2 z-30 px-3 sm:bottom-4 sm:px-6">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 rounded-xl border bg-background/95 p-3 shadow-lg backdrop-blur sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {t.agentManagement.editingSummary
                .replace("{name}", selectedProfile.name)
                .replace("{preset}", formatPresetLabel(profileDraft.capabilityPreset))
                .replace("{scope}", summarizeKnowledgeScope(profileDraft.knowledgePackIds.length))}
            </p>
            <div className="grid grid-cols-2 gap-2 sm:flex">
              <Button
                variant="outline"
                title={canSetWorkspaceDefault ? undefined : t.agentManagement.setDefaultChatOnlyHint}
                onClick={() => setDefaultMutation.mutate()}
                disabled={
                  setDefaultMutation.isPending || selectedProfile.is_default || !canSetWorkspaceDefault
                }
              >
                <Shield className="h-4 w-4" />
                {t.agentManagement.setDefault}
              </Button>
              <Button onClick={() => saveProfileMutation.mutate()} disabled={saveProfileMutation.isPending}>
                <Save className="h-4 w-4" />
                {t.agentManagement.saveProfile}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
