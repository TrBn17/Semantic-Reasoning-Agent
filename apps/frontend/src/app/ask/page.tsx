"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { MessageSquare, Plus } from "lucide-react";
import { toast } from "sonner";
import { useRouteTransition } from "@/components/layout/route-transition-provider";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listAgentProfiles } from "@/lib/api/agent-profiles";
import { createConversation } from "@/lib/api/conversations";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function ChatLandingPage() {
  const { t } = useI18n();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { beginNavigation } = useRouteTransition();
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
        title: t.askLanding.defaultConversationTitle,
        workspace_id: workspaceId ?? undefined,
        agent_profile_id: preferredAgentProfileId ?? undefined,
      }),
    onSuccess: (c) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
      const href = `/ask/${c.id}`;
      beginNavigation(href);
      router.push(href);
    },
    onError: (err) => toast.error(`${t.chat.conversationCreateFailedPrefix} ${(err as Error).message}`),
  });

  return (
    <div className="flex h-full items-center justify-center">
      <div className="max-w-md space-y-4 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <MessageSquare className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-semibold">{t.askLanding.newConversationTitle}</h2>
        <p className="text-sm text-muted-foreground">
          {t.askLanding.newConversationBody}
        </p>
        <Select
          value={preferredAgentProfileId ?? "__default__"}
          onValueChange={(value) =>
            setPreferredAgentProfileId(value === "__default__" ? null : value)
          }
        >
          <SelectTrigger>
            <SelectValue placeholder={t.common.selectProfile} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__default__">{t.common.workspaceDefault}</SelectItem>
            {(profiles ?? []).map((profile) => (
              <SelectItem key={profile.id} value={profile.id}>
                {profile.name}
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
          {t.askLanding.newConversationButton}
        </Button>
      </div>
    </div>
  );
}
