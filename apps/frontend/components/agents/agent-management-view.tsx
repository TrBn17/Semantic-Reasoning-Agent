"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save, Shield } from "lucide-react";
import { toast } from "sonner";
import {
  TaskModelPicker,
  composeModelValue,
  formatPresetLabel,
  parseModelValue,
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
import { getCapabilityCatalog, listCapabilityTools } from "@/lib/api/agent-capabilities";
import {
  createAgentProfile,
  listAgentProfiles,
  setDefaultAgentProfile,
  updateAgentProfile,
} from "@/lib/api/agent-profiles";
import { listDocuments } from "@/lib/api/documents";
import { createKnowledgePack, listKnowledgePacks, updateKnowledgePack } from "@/lib/api/knowledge-packs";
import { listSettingsModels } from "@/lib/api/settings";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import type {
  AgentProfileResponse,
  EvidencePolicySchema,
  KnowledgePackResponse,
  SettingsModelOption,
  ToolPolicySchema,
} from "@/lib/api/types";

type ProfileDraft = {
  description: string;
  systemPrompt: string;
  allowChatOverride: boolean;
  capabilityPreset: string;
  toolPolicyMode: string;
  allowedTools: string;
  blockedTools: string;
  knowledgePackIds: string[];
  allowedSources: string[];
  allowModelOnlyFallback: boolean;
  taskModels: Record<string, string>;
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

function toCsv(values: string[]) {
  return values.join(", ");
}

function fromCsv(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function makeProfileDraft(profile: AgentProfileResponse): ProfileDraft {
  return {
    description: profile.description,
    systemPrompt: profile.system_prompt,
    allowChatOverride: profile.allow_chat_model_override,
    capabilityPreset: profile.capability_preset,
    toolPolicyMode: profile.tool_policy.mode,
    allowedTools: toCsv(profile.tool_policy.allowed_tools),
    blockedTools: toCsv(profile.tool_policy.blocked_tools),
    knowledgePackIds: [...profile.knowledge_pack_ids],
    allowedSources: [...profile.evidence_policy.allowed_sources],
    allowModelOnlyFallback: profile.evidence_policy.allow_model_only_fallback,
    taskModels: Object.fromEntries(
      profile.task_models.map((item) => [item.task_type, composeModelValue(item.provider, item.model)]),
    ),
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
    allowed_tools: fromCsv(draft.allowedTools),
    blocked_tools: fromCsv(draft.blockedTools),
  };
}

function buildEvidencePolicy(draft: ProfileDraft): EvidencePolicySchema {
  return {
    allowed_sources: draft.allowedSources,
    allow_model_only_fallback: draft.allowModelOnlyFallback,
  };
}

export function AgentManagementView() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
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
  const { data: models = [] } = useQuery({
    queryKey: queryKeys.settings.models(workspaceId),
    queryFn: () => listSettingsModels(workspaceId),
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
  const knowledgeById = useMemo(
    () => Object.fromEntries(knowledgePacks.map((pack) => [pack.id, pack])),
    [knowledgePacks],
  );
  const profileToolSummary = useMemo(() => {
    if (!profileDraft || !selectedPreset) return [];
    return capabilityTools.filter((tool) => selectedPreset.allowed_tool_families.includes(tool.family));
  }, [capabilityTools, profileDraft, selectedPreset]);
  const taskTypes = [
    { task_type: "chat", label: "Chat" },
    { task_type: "retrieval", label: "Retrieval QA" },
    { task_type: "ontology_extraction", label: "Ontology Extraction" },
    { task_type: "narrative_generation", label: "Narrative" },
    { task_type: "dashboard_generation", label: "Dashboard" },
  ] as const;

  const createProfileMutation = useMutation({
    mutationFn: () =>
      createAgentProfile({
        workspace_id: workspaceId ?? "workspace-demo",
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
      }),
    onSuccess: async (profile) => {
      setNewProfileName("");
      setSelectedProfileId(profile.id);
      setPreferredAgentProfileId(profile.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success("Agent profile created.");
    },
    onError: (error) => toast.error(`Create failed: ${(error as Error).message}`),
  });

  const saveProfileMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile || !profileDraft) {
        throw new Error("Select a profile first.");
      }
      return updateAgentProfile(selectedProfile.id, {
        description: profileDraft.description,
        system_prompt: profileDraft.systemPrompt,
        allow_chat_model_override: profileDraft.allowChatOverride,
        capability_preset: profileDraft.capabilityPreset,
        tool_policy: buildToolPolicy(profileDraft),
        knowledge_pack_ids: profileDraft.knowledgePackIds,
        evidence_policy: buildEvidencePolicy(profileDraft),
        task_models: taskTypes
          .map((task) => {
            const parsed = parseModelValue(profileDraft.taskModels[task.task_type]);
            if (!parsed) return null;
            return { task_type: task.task_type, provider: parsed.provider, model: parsed.model };
          })
          .filter((item): item is NonNullable<typeof item> => Boolean(item)),
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success("Profile saved.");
    },
    onError: (error) => toast.error(`Save failed: ${(error as Error).message}`),
  });

  const setDefaultMutation = useMutation({
    mutationFn: () => {
      if (!selectedProfile) throw new Error("Select a profile first.");
      return setDefaultAgentProfile(selectedProfile.id);
    },
    onSuccess: async (profile) => {
      setPreferredAgentProfileId(profile.id);
      await queryClient.invalidateQueries({ queryKey: queryKeys.agents.profiles(workspaceId) });
      toast.success("Default profile updated.");
    },
    onError: (error) => toast.error(`Default update failed: ${(error as Error).message}`),
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
      return createKnowledgePack({
        workspace_id: workspaceId ?? "workspace-demo",
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
      toast.success("Knowledge pack saved.");
    },
    onError: (error) => toast.error(`Knowledge pack save failed: ${(error as Error).message}`),
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
          <CardTitle>Agent Management</CardTitle>
          <CardDescription>
            Manage profiles, capability presets, tool policy, knowledge packs, and evidence scope from a single control plane.
          </CardDescription>
        </CardHeader>
      </Card>

      <div className="grid items-start gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Profiles</CardTitle>
            <CardDescription>Create profiles here. Provider credentials belong in `/settings`.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={newProfileName}
                onChange={(event) => setNewProfileName(event.target.value)}
                placeholder="New profile name"
              />
              <Button
                onClick={() => createProfileMutation.mutate()}
                disabled={createProfileMutation.isPending || !newProfileName.trim()}
              >
                <Plus className="h-4 w-4" />
                Create
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
                    {profile.is_default && <Badge variant="success">Default</Badge>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {profile.description || "No description"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>{formatPresetLabel(profile.capability_preset)}</span>
                    <span>{summarizeKnowledgeScope(profile.knowledge_pack_ids.length)}</span>
                  </div>
                </button>
              ))}
              {(profiles ?? []).length === 0 && (
                <div className="rounded-2xl border border-dashed p-6 text-sm text-muted-foreground">
                  No profiles yet. Create one to define capability preset, tool policy, and knowledge scope.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {!selectedProfile || !profileDraft ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Select a profile to edit identity, capability, knowledge scope, evidence policy, and advanced model overrides.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Identity</CardTitle>
                <CardDescription>Core agent identity and prompt contract.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input value={selectedProfile.name} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Input value={selectedProfile.status} disabled />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Input
                    value={profileDraft.description}
                    onChange={(event) =>
                      setProfileDraft((current) => (current ? { ...current, description: event.target.value } : current))
                    }
                    placeholder="What this agent is for"
                  />
                </div>
                <div className="space-y-2">
                  <Label>System prompt</Label>
                  <Textarea
                    value={profileDraft.systemPrompt}
                    onChange={(event) =>
                      setProfileDraft((current) => (current ? { ...current, systemPrompt: event.target.value } : current))
                    }
                    className="min-h-[160px]"
                    placeholder="You are an analyst agent..."
                  />
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={profileDraft.allowChatOverride}
                    onChange={(event) =>
                      setProfileDraft((current) =>
                        current ? { ...current, allowChatOverride: event.target.checked } : current,
                      )
                    }
                  />
                  Allow per-conversation model override
                </label>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Capability</CardTitle>
                <CardDescription>Select the preset first, then narrow tool access inside that preset.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Capability preset</Label>
                  <Select
                    value={profileDraft.capabilityPreset}
                    onValueChange={(value) =>
                      setProfileDraft((current) => (current ? { ...current, capabilityPreset: value } : current))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select preset" />
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
                        <Badge key={family} variant="outline">{family}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Tool policy mode</Label>
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
                        <SelectItem value="preset">Preset</SelectItem>
                        <SelectItem value="allowlist">Allowlist</SelectItem>
                        <SelectItem value="blocklist">Blocklist</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Preset summary</Label>
                    <Input value={selectedPreset?.default_tool_order.join(", ") ?? "No preset selected"} disabled />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Allowed tools</Label>
                    <Input
                      value={profileDraft.allowedTools}
                      onChange={(event) =>
                        setProfileDraft((current) => (current ? { ...current, allowedTools: event.target.value } : current))
                      }
                      placeholder="retrieval.internal, ontology.lookup"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Blocked tools</Label>
                    <Input
                      value={profileDraft.blockedTools}
                      onChange={(event) =>
                        setProfileDraft((current) => (current ? { ...current, blockedTools: event.target.value } : current))
                      }
                      placeholder="graphiti.search"
                    />
                  </div>
                </div>

                <div className="rounded-2xl border p-4">
                  <h3 className="font-semibold">Visible tools for this preset</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {profileToolSummary.map((tool) => (
                      <div key={tool.tool_name} className="rounded-xl border p-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{tool.label}</span>
                          <Badge variant="outline">{tool.family}</Badge>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{tool.description}</p>
                      </div>
                    ))}
                    {profileToolSummary.length === 0 && (
                      <div className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                        No tool catalog entries matched this preset yet.
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Knowledge Scope</CardTitle>
                  <CardDescription>Select packs for the profile and create or edit packs inline.</CardDescription>
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
                      New pack
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>{editingPack ? "Edit knowledge pack" : "Create knowledge pack"}</DialogTitle>
                      <DialogDescription>Knowledge packs stay inside the `/agents` workflow.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label>Name</Label>
                          <Input
                            value={knowledgePackDraft.name}
                            onChange={(event) =>
                              setKnowledgePackDraft((current) => ({ ...current, name: event.target.value }))
                            }
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Status</Label>
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
                              <SelectItem value="active">Active</SelectItem>
                              <SelectItem value="archived">Archived</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Description</Label>
                        <Textarea
                          value={knowledgePackDraft.description}
                          onChange={(event) =>
                            setKnowledgePackDraft((current) => ({ ...current, description: event.target.value }))
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Documents</Label>
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
                        Cancel
                      </Button>
                      <Button
                        onClick={() => saveKnowledgePackMutation.mutate()}
                        disabled={saveKnowledgePackMutation.isPending || !knowledgePackDraft.name.trim()}
                      >
                        Save knowledge pack
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
                            <p className="mt-1 text-sm text-muted-foreground">{pack.description || "No description"}</p>
                            <p className="mt-2 text-xs text-muted-foreground">
                              {pack.document_ids.length} linked documents
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
                            Edit
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
                          Attach to this profile
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
                    No knowledge packs yet. Create one here and attach documents before assigning it to a profile.
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence Policy</CardTitle>
                <CardDescription>Control which evidence sources the profile may rely on.</CardDescription>
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
                  Allow model-only fallback when policy permits
                </label>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Advanced Model Overrides</CardTitle>
                <CardDescription>Optional per-task overrides. Keep this secondary to capability and knowledge scope.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {taskTypes.map((task) => (
                  <div key={task.task_type} className="rounded-2xl border p-4">
                    <div className="mb-3">
                      <h3 className="font-semibold">{task.label}</h3>
                      <p className="text-sm text-muted-foreground">
                        Leave empty to inherit workspace defaults from `/settings`.
                      </p>
                    </div>
                    <TaskModelPicker
                      models={models}
                      value={profileDraft.taskModels[task.task_type]}
                      onChange={(value) =>
                        setProfileDraft((current) =>
                          current
                            ? {
                                ...current,
                                taskModels: { ...current.taskModels, [task.task_type]: value },
                              }
                            : current,
                        )
                      }
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {selectedProfile && profileDraft && (
        <div className="fixed inset-x-0 bottom-2 z-30 px-3 sm:bottom-4 sm:px-6">
          <div className="mx-auto flex max-w-6xl flex-col gap-3 rounded-xl border bg-background/95 p-3 shadow-lg backdrop-blur sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Editing `{selectedProfile.name}` with {formatPresetLabel(profileDraft.capabilityPreset)} and {summarizeKnowledgeScope(profileDraft.knowledgePackIds.length)}.
            </p>
            <div className="grid grid-cols-2 gap-2 sm:flex">
              <Button
                variant="outline"
                onClick={() => setDefaultMutation.mutate()}
                disabled={setDefaultMutation.isPending || selectedProfile.is_default}
              >
                <Shield className="h-4 w-4" />
                Set default
              </Button>
              <Button onClick={() => saveProfileMutation.mutate()} disabled={saveProfileMutation.isPending}>
                <Save className="h-4 w-4" />
                Save profile
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
