"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, CircleAlert, Search } from "lucide-react";
import { toast } from "sonner";
import {
  updateConversationAgentProfile,
  updateConversationModelSelection,
} from "@/shared/api/conversations";
import { listAgentProfiles } from "@/shared/api/agent-profiles";
import type { ConversationResponse, ModelOption } from "@/shared/api/types";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function composeValue(provider: string, model: string) {
  return `${provider}::${model}`;
}

export function ChatRuntimeControls({
  conversation,
  models,
  onConversationChange,
}: {
  conversation: ConversationResponse;
  models: ModelOption[];
  onConversationChange: (conversation: ConversationResponse) => void;
}) {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [search, setSearch] = useState("");
  const { data: profiles } = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });

  const updateModelMutation = useMutation({
    mutationFn: (value: string) => {
      const [provider, model] = value.split("::");
      return updateConversationModelSelection(conversation.id, {
        provider,
        model,
        workspace_id: conversation.workspace_id,
      });
    },
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`Model update failed: ${(err as Error).message}`),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (profileId: string) =>
      updateConversationAgentProfile(conversation.id, {
        agent_profile_id: profileId || null,
        workspace_id: conversation.workspace_id,
        clear_model_override: true,
      }),
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`Profile update failed: ${(err as Error).message}`),
  });

  const activeProfile = profiles?.find((item) => item.id === conversation.agent_profile_id);
  const allowOverride = activeProfile?.allow_chat_model_override ?? true;
  const filteredModels = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return models
      .filter((model) => {
        if (!keyword) return true;
        return [model.provider, model.model, model.label, model.description]
          .join(" ")
          .toLowerCase()
          .includes(keyword);
      })
      .sort((a, b) => {
        if (a.ready !== b.ready) {
          return a.ready ? -1 : 1;
        }
        return a.label.localeCompare(b.label);
      });
  }, [models, search]);

  return (
    <div className="space-y-3 rounded-2xl border bg-background/80 p-3 shadow-sm">
      <div className="grid gap-3 lg:grid-cols-[220px_minmax(0,1fr)]">
        <Select
          value={conversation.agent_profile_id ?? "__workspace__"}
          onValueChange={(value) =>
            updateProfileMutation.mutate(value === "__workspace__" ? "" : value)
          }
        >
          <SelectTrigger className="rounded-xl">
            <SelectValue placeholder="Select profile" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__workspace__">Workspace default</SelectItem>
            {(profiles ?? []).map((profile) => (
              <SelectItem key={profile.id} value={profile.id}>
                {profile.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="space-y-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search provider or model"
              className="rounded-xl pl-9"
            />
          </div>
          <Select
            value={composeValue(conversation.provider, conversation.model)}
            onValueChange={(value) => updateModelMutation.mutate(value)}
            disabled={!allowOverride}
          >
            <SelectTrigger className="rounded-xl">
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              {filteredModels.map((model) => (
                <SelectItem
                  key={composeValue(model.provider, model.model)}
                  value={composeValue(model.provider, model.model)}
                >
                  <span className="flex items-center gap-2">
                    {model.ready ? (
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                    ) : (
                      <CircleAlert className="h-3.5 w-3.5 text-amber-500" />
                    )}
                    <span>{model.label}</span>
                    <span className="text-xs text-muted-foreground">· {model.provider}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={conversation.uses_model_override ? "info" : "outline"}>
          {conversation.uses_model_override ? "Session override" : "Inherited default"}
        </Badge>
        <Badge variant="outline">{conversation.provider}</Badge>
        <Badge variant="outline">{conversation.model}</Badge>
        {conversation.effective_agent_name && (
          <Badge variant="outline">Agent: {conversation.effective_agent_name}</Badge>
        )}
        {!allowOverride && <Badge variant="warning">Profile locks model override</Badge>}
        {conversation.effective_tool_names.slice(0, 4).map((toolName) => (
          <Badge key={toolName} variant="outline" className="font-mono text-[11px]">
            {toolName}
          </Badge>
        ))}
      </div>
    </div>
  );
}
