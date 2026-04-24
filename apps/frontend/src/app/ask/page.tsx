"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatPresetLabel, summarizeKnowledgeScope } from "@/components/agents/model-picker";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAgentProfiles } from "@/shared/api/agent-profiles";
import { createConversation } from "@/shared/api/conversations";
import { queryKeys } from "@/shared/query/keys";
import { useI18n } from "@/shared/i18n/use-language";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { notify } from "@/shared/ui/notify";

export default function ChatLandingPage() {
  const { t } = useI18n();
  const router = useRouter();
  const queryClient = useQueryClient();
  const {
    workspaceId,
    preferredAgentProfileId,
    setPreferredAgentProfileId,
  } = useWorkspaceStore();
  const { data: profiles } = useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });

  const mutation = useMutation({
    mutationFn: () =>
      createConversation({
        title: t.pages.ask.newConversationTitle,
        workspace_id: workspaceId ?? undefined,
        agent_profile_id: preferredAgentProfileId ?? undefined,
      }),
    onSuccess: (c) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
      router.push(`/ask/${c.id}`);
    },
    onError: (err) => notify.error(`${t.pages.ask.createFailedPrefix} ${(err as Error).message}`, t.common.error),
  });

  return (
    <div className="flex h-full items-center justify-center">
      <div className="max-w-md space-y-4 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <MessageSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold">{t.pages.ask.newConversationHeading}</h2>
        <Select
          value={preferredAgentProfileId ?? "__default__"}
          onValueChange={(value) =>
            setPreferredAgentProfileId(value === "__default__" ? null : value)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t.chatRuntimeControls.selectProfile} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__default__">{t.pages.ask.workspaceDefault}</SelectItem>
            {(profiles ?? []).map((profile) => (
              <SelectItem key={profile.id} value={profile.id}>
                {`${profile.name} · ${formatPresetLabel(profile.capability_preset)} · ${summarizeKnowledgeScope(profile.knowledge_pack_ids.length)}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          size="lg"
        >
          <Plus className="h-4 w-4" />
          {t.pages.ask.newConversationButton}
        </Button>
      </div>
    </div>
  );
}
