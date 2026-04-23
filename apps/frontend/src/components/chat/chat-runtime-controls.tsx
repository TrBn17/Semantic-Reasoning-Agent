"use client";

import { useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { ModelCombobox } from "@/components/agents/model-combobox";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAgentProfiles } from "@/shared/api/agent-profiles";
import {
  updateConversationAgentProfile,
  updateConversationModelSelection,
} from "@/shared/api/conversations";
import type { ConversationResponse, SettingsModelOption } from "@/shared/api/types";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { composeModelValue } from "@/shared/utils/model-value";

export function ChatRuntimeControls({
  conversation,
  models,
  onConversationChange,
}: {
  conversation: ConversationResponse;
  models: SettingsModelOption[];
  onConversationChange: (conversation: ConversationResponse) => void;
}) {
  const { t } = useI18n();
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
    onError: (err) => toast.error(`${t.agentsSettings.toasts.saveFailedPrefix} ${(err as Error).message}`),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (profileId: string) =>
      updateConversationAgentProfile(conversation.id, {
        agent_profile_id: profileId || null,
        workspace_id: conversation.workspace_id,
        clear_model_override: true,
      }),
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`${t.agentsSettings.toasts.profileSaveFailedPrefix} ${(err as Error).message}`),
  });

  const sortedModels = useMemo(() => {
    return [...models].sort((a, b) => {
      if (a.ready !== b.ready) {
        return a.ready ? -1 : 1;
      }
      return a.label.localeCompare(b.label);
    });
  }, [models]);

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
            <SelectValue placeholder={t.chatRuntimeControls.selectProfile} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__workspace__">{t.chatRuntimeControls.noProfile}</SelectItem>
            {(profiles ?? []).map((profile) => (
              <SelectItem key={profile.id} value={profile.id}>
                {profile.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <ModelCombobox
          models={sortedModels}
          value={composeModelValue(conversation.provider, conversation.model)}
          onChange={(value) => updateModelMutation.mutate(value)}
          labels={{
            providerPlaceholder: t.agentsSettings.picker.providerPlaceholder,
            allProviders: t.agentsSettings.picker.allProviders,
            searchModelPlaceholder: t.chatRuntimeControls.searchProviderModel,
            selectModelPlaceholder: t.chatRuntimeControls.selectModel,
            noModelMatch: t.agentsSettings.picker.noModelMatch,
            assignmentUnavailable: t.agentsSettings.picker.assignmentUnavailable,
            readyBadge: t.agentsSettings.taskRouting.ready,
            blockedBadge: t.agentsSettings.taskRouting.blocked,
            capabilityStreaming: t.agentsSettings.taskRouting.streaming,
            capabilityStructured: t.agentsSettings.taskRouting.structuredOutput,
          }}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{conversation.provider}</Badge>
        <Badge variant="outline">{conversation.model}</Badge>
        {conversation.effective_agent_name && (
          <Badge variant="outline">
            {t.chatRuntimeControls.agentPrefix}: {conversation.effective_agent_name}
          </Badge>
        )}
        {conversation.effective_tool_names.slice(0, 4).map((toolName) => (
          <Badge key={toolName} variant="outline" className="font-mono text-[11px]">
            {toolName}
          </Badge>
        ))}
      </div>
    </div>
  );
}
