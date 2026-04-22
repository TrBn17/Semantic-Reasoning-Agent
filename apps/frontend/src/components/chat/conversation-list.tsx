"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Time } from "@/shared/components/time";
import { cn } from "@/shared/utils";
import {
  createConversation,
  listConversations,
} from "@/shared/api/conversations";
import { listAgentProfiles } from "@/shared/api/agent-profiles";
import { queryKeys } from "@/shared/query/keys";
import { useI18n } from "@/shared/i18n/use-language";
import { useWorkspaceStore } from "@/shared/state/workspace-store";

export function ConversationList() {
  const params = useParams<{ conversationId?: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const { workspaceId, preferredAgentProfileId } = useWorkspaceStore();

  const {
    data: conversations,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.conversations.list(),
    queryFn: listConversations,
  });
  useQuery({
    queryKey: queryKeys.agents.profiles(workspaceId),
    queryFn: () => listAgentProfiles(workspaceId),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createConversation({
        title: t.conversationList.newConversationTitle,
        workspace_id: workspaceId ?? undefined,
        agent_profile_id: preferredAgentProfileId ?? undefined,
      }),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.all });
      router.push(`/ask/${conversation.id}`);
      toast.success(t.conversationList.created);
    },
    onError: (err) => toast.error(`${t.conversationList.createFailedPrefix} ${(err as Error).message}`),
  });

  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r bg-muted/20">
      <div className="flex items-center justify-between border-b p-3">
        <span className="text-sm font-semibold">{t.conversationList.title}</span>
        <Button
          size="sm"
          onClick={() => createMutation.mutate()}
          disabled={createMutation.isPending}
        >
          <Plus className="h-4 w-4" />
          {t.conversationList.newConversation}
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {isLoading &&
            Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          {isError && (
            <p className="p-3 text-sm text-destructive">
              {t.conversationList.loadFailed}
            </p>
          )}
          {conversations?.length === 0 && (
            <p className="p-3 text-sm text-muted-foreground">
              {t.conversationList.empty}
            </p>
          )}
          {conversations?.map((c) => {
            const active = params?.conversationId === c.id;
            return (
              <Link
                key={c.id}
                href={`/ask/${c.id}`}
                className={cn(
                  "block rounded-md px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent",
                )}
              >
                <div className="truncate font-medium">{c.title}</div>
                <div
                  className={cn(
                    "truncate text-xs",
                    active ? "text-primary-foreground/70" : "text-muted-foreground",
                  )}
                >
                  {c.provider} · {c.model} · <Time value={c.updated_at} className="inline" />
                </div>
              </Link>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
