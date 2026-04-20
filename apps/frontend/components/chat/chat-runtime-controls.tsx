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
import { useI18n } from "@/src/shared/i18n/use-language";
import { composeProviderModel, parseProviderModelValue } from "@/lib/model-routing";

export function ChatRuntimeControls({
  conversation,
  models,
  onConversationChange,
}: {
  conversation: ConversationResponse;
  models: ModelOption[];
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
      const parsed = parseProviderModelValue(value);
      if (!parsed) throw new Error("Invalid model selection");
      return updateConversationModelSelection(conversation.id, {
        provider: parsed.provider,
        model: parsed.model,
        workspace_id: conversation.workspace_id,
      });
    },
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`${t.common.modelUpdateFailedPrefix} ${(err as Error).message}`),
  });

  const updateProfileMutation = useMutation({
    mutationFn: (profileId: string) =>
      updateConversationAgentProfile(conversation.id, {
        agent_profile_id: profileId || null,
        workspace_id: conversation.workspace_id,
        clear_model_override: !conversation.uses_model_override,
      }),
    onSuccess: onConversationChange,
    onError: (err) => toast.error(`${t.common.profileUpdateFailedPrefix} ${(err as Error).message}`),
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
          <SelectValue placeholder={t.common.selectProfile} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__workspace__">{t.common.workspaceDefault}</SelectItem>
          {(profiles ?? []).map((profile) => (
            <SelectItem key={profile.id} value={profile.id}>
              {profile.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={composeProviderModel(conversation.provider, conversation.model)}
        onValueChange={(value) => updateModelMutation.mutate(value)}
        disabled={!allowOverride}
      >
        <SelectTrigger className="w-[240px]">
          <SelectValue placeholder={t.common.selectModel} />
        </SelectTrigger>
        <SelectContent>
          {Object.entries(grouped).map(([providerName, opts]) => (
            <SelectGroup key={providerName}>
              <SelectLabel className="capitalize">{providerName}</SelectLabel>
              {opts.map((opt) => (
                <SelectItem
                  key={composeProviderModel(opt.provider, opt.model)}
                  value={composeProviderModel(opt.provider, opt.model)}
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
        {conversation.uses_model_override ? t.common.sessionOverride : t.common.inheritedDefault}
      </Badge>
      {!allowOverride && <Badge variant="warning">{t.common.profileLocksModelOverride}</Badge>}
    </div>
  );
}
