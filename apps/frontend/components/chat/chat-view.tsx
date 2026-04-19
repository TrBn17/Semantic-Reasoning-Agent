"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useState } from "react";
import { toast } from "sonner";
import { ChatRuntimeControls } from "@/components/chat/chat-runtime-controls";
import {
  MessageComposer,
  type ComposerSubmitPayload,
} from "@/components/chat/message-composer";
import { MessageThread } from "@/components/chat/message-thread";
import { Skeleton } from "@/components/ui/skeleton";
import { sendMessage } from "@/lib/api/chat";
import { getConversation } from "@/lib/api/conversations";
import { listModels } from "@/lib/api/models";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import type { Citation } from "@/lib/api/types";

const CitationsDrawer = dynamic(
  () =>
    import("@/components/chat/citations-drawer").then((m) => ({
      default: m.CitationsDrawer,
    })),
  { ssr: false, loading: () => null },
);

export function ChatView({ conversationId }: { conversationId: string }) {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [latestCitations, setLatestCitations] = useState<Citation[]>([]);

  const { data: conversation, isLoading } = useQuery({
    queryKey: queryKeys.conversations.detail(conversationId),
    queryFn: () => getConversation(conversationId),
  });

  const { data: models = [] } = useQuery({
    queryKey: [...queryKeys.models, workspaceId ?? null],
    queryFn: () => listModels(workspaceId),
  });

  const mutation = useMutation({
    mutationFn: (payload: ComposerSubmitPayload) =>
      sendMessage({
        conversation_id: conversationId,
        content: payload.content,
        use_retrieval: payload.useRetrieval,
        workspace_id: workspaceId ?? conversation?.workspace_id ?? undefined,
        document_ids: payload.documentIds,
        top_k: payload.topK,
      }),
    onSuccess: (reply) => {
      queryClient.setQueryData(
        queryKeys.conversations.detail(conversationId),
        reply.conversation,
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations.list() });
      setLatestCitations(reply.citations ?? []);
    },
    onError: (err) => toast.error(`Failed to send: ${(err as Error).message}`),
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-start justify-between gap-4 border-b bg-muted/20 px-6 py-3">
        <div className="space-y-2">
          <div>
            <h2 className="font-semibold">{conversation?.title ?? "Conversation"}</h2>
            <p className="text-xs text-muted-foreground">
              {conversation ? `${conversation.provider} · ${conversation.model}` : ""}
            </p>
          </div>
          {conversation && (
            <ChatRuntimeControls
              conversation={conversation}
              models={models}
              onConversationChange={(updated) => {
                queryClient.setQueryData(
                  queryKeys.conversations.detail(conversationId),
                  updated,
                );
                queryClient.invalidateQueries({ queryKey: queryKeys.conversations.list() });
              }}
            />
          )}
        </div>
        <CitationsDrawer citations={latestCitations} />
      </div>
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {isLoading && (
          <div className="space-y-3">
            <Skeleton className="h-16 w-2/3" />
            <Skeleton className="h-16 w-1/2" />
          </div>
        )}
        {conversation && (
          <MessageThread messages={conversation.messages} isPending={mutation.isPending} />
        )}
      </div>
      <MessageComposer
        onSubmit={(payload) => mutation.mutate(payload)}
        disabled={mutation.isPending}
      />
    </div>
  );
}
