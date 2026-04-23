"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save, Shield } from "lucide-react";
import { toast } from "sonner";
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
import { ToolDndBoard } from "@/components/agents/tool-dnd-board";
import { getCapabilityCatalog, listCapabilityTools } from "@/shared/api/agent-capabilities";
import {
  createAgentProfile,
  listAgentProfiles,
  setDefaultAgentProfile,
  updateAgentProfile,
} from "@/shared/api/agent-profiles";
import { listDocuments } from "@/shared/api/documents";
import { createKnowledgePack, listKnowledgePacks, updateKnowledgePack } from "@/shared/api/knowledge-packs";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import type {
  AgentProfileResponse,
  EvidencePolicySchema,
  KnowledgePackResponse,
  ToolPolicySchema,
} from "@/shared/api/types";

type ProfileDraft = {
  description: string;
  systemPrompt: string;
  capabilityPreset: string;
  toolPolicyMode: string;
  allowedTools: string[];
  blockedTools: string[];
  knowledgePackIds: string[];
  allowedSources: string[];
  allowModelOnlyFallback: boolean;
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
  return {
    description: profile.description,
    systemPrompt: profile.system_prompt,
    capabilityPreset: profile.capability_preset,
    toolPolicyMode: profile.tool_policy.mode,
    allowedTools: [...profile.tool_policy.allowed_tools],
    blockedTools: [...profile.tool_policy.blocked_tools],
    knowledgePackIds: [...profile.knowledge_pack_ids],
    allowedSources: [...profile.evidence_policy.allowed_sources],
    allowModelOnlyFallback: profile.evidence_policy.allow_model_only_fallback,
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
  const { data: capabilityTools = [] } = useQuery({
    queryKey: queryKeys.capabilities.tools(),
    queryFn: listCapabilityTools,
  });
  const { data: knowledgePacks = [] } = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
  });
  const { data: documents = [] } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });

  const [newProfileName, setNewProfileName] = useState("");
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [profileDraft, setProfileDraft] = useState<ProfileDraft | null>(null);
  const [knowledgeDialogOpen, setKnowledgeDialogOpen] = useState(false);
  const [editingPack, setEditingPack] = useState<KnowledgePackResponse | null>(null);
  const [knowledgePackDraft, setKnowledgePackDraft] = useState<KnowledgePackDraft>(makeKnowledgePackDraft());

  useEffect(() => {
    const selected =
      profiles?.find((item) => item.id === selectedProfileId) ??
      profiles?.find((item) => item.id === preferredAgentProfileId) ??
      profiles?.find((item) => item.is_default) ??
      profiles?.[0];
    if (!selected) return;
    setSelectedProfileId(selected.id);
    setPreferredAgentProfileId(selected.id);
    setProfileDraft(makeProfileDraft(selected));
  }, [preferredAgentProfileId, profiles, selectedProfileId, setPreferredAgentProfileId]);

  const selectedProfile = useMemo(
    () => profiles?.find((item) => item.id === selectedProfileId) ?? null,
    [profiles, selectedProfileId],
  );
  const selectedPreset = useMemo(
    () => capabilityCatalog?.presets.find((item) => item.preset === profileDraft?.capabilityPreset) ?? null,
    [capabilityCatalog?.presets, profileDraft?.capabilityPreset],
  );
  const profileToolSummary = useMemo(() => {
    if (!profileDraft || !selectedPreset) return [];
    return capabilityTools.filter((tool) => selectedPreset.allowed_tool_families.includes(tool.family));
  }, [capabilityTools, profileDraft, selectedPreset]);

  const createProfileMutation = useMutation({
    mutationFn: () => {
      if (!workspaceId) {
        throw new Error("Workspace is not resolved.");
      }
      return createAgentProfile({
        workspace_id: workspaceId,
        name: newProfileName.trim(),
        description: "",
        system_prompt: "",
        allow_chat_model_override: true,
        capability_preset: capabilityCatalog?.presets[0]?.preset ?? "internal_qa",
        tool_policy: { mode: "preset", allowed_tools: [], blocked_tools: [] },
        knowledge_pack_ids: [],
        evidence_policy: {
          allowed_sources: ["internal_chunk", "graph_node", "graph_edge"],
          allow_model_only_fallback: true,
        },
        task_models: [],
      });
    },
    onSuccess: async (profile) => {
      setNewProfileName("");
      setSelectedProfileId(profile.id);
      setPreferredAgentProfileId(profile.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success(t.agentsSettings.toasts.agentProfileCreated);
    },
    onError: (error) => toast.error(`${t.agentsSettings.toasts.createFailedPrefix} ${(error as Error).message}`),
  });

  const saveProfileMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile || !profileDraft) {
        throw new Error("Select a profile first.");
      }
      return updateAgentProfile(selectedProfile.id, {
        description: profileDraft.description,
        system_prompt: profileDraft.systemPrompt,
        allow_chat_model_override: true,
        capability_preset: profileDraft.capabilityPreset,
        tool_policy: buildToolPolicy(profileDraft),
        knowledge_pack_ids: profileDraft.knowledgePackIds,
        evidence_policy: buildEvidencePolicy(profileDraft),
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success(t.agentsSettings.toasts.profileSaved);
    },
    onError: (error) => toast.error(`${t.agentsSettings.toasts.profileSaveFailedPrefix} ${(error as Error).message}`),
  });

  const setDefaultMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile) throw new Error("Select a profile first.");
      return setDefaultAgentProfile(selectedProfile.id);
    },
    onSuccess: async (profile) => {
      setPreferredAgentProfileId(profile.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success(t.agentsSettings.toasts.defaultProfileUpdated);
    },
    onError: (error) => toast.error(`${t.agentsSettings.toasts.defaultUpdateFailedPrefix} ${(error as Error).message}`),
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
      toast.success(t.agentManagement.toastKnowledgePackSaved);
    },
    onError: (error) =>
      toast.error(`${t.agentManagement.toastKnowledgePackSaveFailedPrefix} ${(error as Error).message}`),
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
            <div className="flex gap-2">
              <Input
                value={newProfileName}
                onChange={(event) => setNewProfileName(event.target.value)}
                placeholder={t.agentManagement.newProfilePlaceholder}
              />
              <Button
                onClick={() => createProfileMutation.mutate()}
                disabled={createProfileMutation.isPending || !newProfileName.trim()}
              >
                <Plus className="h-4 w-4" />
                {t.agentManagement.create}
              </Button>
            </div>

            <div className="space-y-2">
              {(profiles ?? []).map((profile) => (
                <button
                  key={profile.id}
                  type="button"
                  onClick={() => {
                    setSelectedProfileId(profile.id);
                    setPreferredAgentProfileId(profile.id);
                    setProfileDraft(makeProfileDraft(profile));
                  }}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    selectedProfileId === profile.id
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "hover:border-primary/40"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{profile.name}</span>
                    {profile.is_default && <Badge variant="success">{t.agentManagement.defaultBadge}</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {profile.description || t.agentManagement.noDescription}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{formatPresetLabel(profile.capability_preset)}</span>
                    <span>{summarizeKnowledgeScope(profile.knowledge_pack_ids.length)}</span>
                  </div>
                </button>
              ))}
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
                <CardTitle>{t.agentManagement.identityTitle}</CardTitle>
                <CardDescription>{t.agentManagement.identityDescription}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>{t.agentManagement.name}</Label>
                    <Input value={selectedProfile.name} disabled />
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

                <ToolDndBoard
                  paletteTools={profileToolSummary}
                  allowedToolNames={profileDraft.allowedTools}
                  blockedToolNames={profileDraft.blockedTools}
                  onAllowedChange={(names) =>
                    setProfileDraft((current) => (current ? { ...current, allowedTools: names } : current))
                  }
                  onBlockedChange={(names) =>
                    setProfileDraft((current) => (current ? { ...current, blockedTools: names } : current))
                  }
                  labels={{
                    lanePalette: t.agentManagement.lanePalette,
                    lanePaletteHint: t.agentManagement.lanePaletteHint,
                    laneAllowed: t.agentManagement.laneAllowed,
                    laneAllowedHint: t.agentManagement.laneAllowedHint,
                    laneBlocked: t.agentManagement.laneBlocked,
                    laneBlockedHint: t.agentManagement.laneBlockedHint,
                    searchToolsPlaceholder: t.agentManagement.searchToolsPlaceholder,
                    riskFilter: t.agentManagement.riskFilter,
                    riskAll: t.agentManagement.riskAll,
                    riskLow: t.agentManagement.riskLow,
                    riskMedium: t.agentManagement.riskMedium,
                    riskHigh: t.agentManagement.riskHigh,
                    removeFromLane: t.agentManagement.removeFromLane,
                    noCatalogTools: t.agentManagement.noCatalogTools,
                  }}
                />
              </CardContent>
            </Card>

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
                onClick={() => setDefaultMutation.mutate()}
                disabled={setDefaultMutation.isPending || selectedProfile.is_default}
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
