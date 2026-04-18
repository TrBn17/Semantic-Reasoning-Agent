"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, CircleAlert } from "lucide-react";
import { toast } from "sonner";
import {
  updateConversationAgentProfile,
  updateConversationModelSelection,
} from "@/lib/api/conversations";
import { listAgentProfiles } from "@/lib/api/agent-profiles";
import type { ConversationResponse, ModelOption } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
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
        clear_model_override: !conversation.uses_model_override,
      }),
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`Profile update failed: ${(err as Error).message}`),
  });

  const grouped: Record<string, ModelOption[]> = {};
  for (const opt of models) {
    grouped[opt.provider] = grouped[opt.provider] ?? [];
    grouped[opt.provider].push(opt);
  }

  const activeProfile = profiles?.find((item) => item.id === conversation.agent_profile_id);
  const allowOverride = activeProfile?.allow_chat_model_override ?? true;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Select
        value={conversation.agent_profile_id ?? "__workspace__"}
        onValueChange={(value) =>
          updateProfileMutation.mutate(value === "__workspace__" ? "" : value)
        }
      >
        <SelectTrigger className="w-[220px]">
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

      <Select
        value={composeValue(conversation.provider, conversation.model)}
        onValueChange={(value) => updateModelMutation.mutate(value)}
        disabled={!allowOverride}
      >
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          {Object.entries(grouped).map(([providerName, opts]) => (
            <SelectGroup key={providerName}>
              <SelectLabel className="capitalize">{providerName}</SelectLabel>
              {opts.map((opt) => (
                <SelectItem
                  key={composeValue(opt.provider, opt.model)}
                  value={composeValue(opt.provider, opt.model)}
                >
                  <span className="flex items-center gap-2">
                    {opt.ready ? (
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                    ) : (
                      <CircleAlert className="h-3.5 w-3.5 text-amber-500" />
                    )}
                    <span>{opt.label}</span>
                  </span>
                </SelectItem>
              ))}
            </SelectGroup>
          ))}
        </SelectContent>
      </Select>

      <Badge variant={conversation.uses_model_override ? "info" : "outline"}>
        {conversation.uses_model_override ? "Session override" : "Inherited default"}
      </Badge>
      {!allowOverride && <Badge variant="warning">Profile locks model override</Badge>}
    </div>
  );
}
