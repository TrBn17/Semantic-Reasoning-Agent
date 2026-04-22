"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { Bot, Wrench } from "lucide-react";
import { toast } from "sonner";
import { ChatRuntimeControls } from "@/components/chat/chat-runtime-controls";
import {
  MessageComposer,
  type ComposerSubmitPayload,
} from "@/components/chat/message-composer";
import { MessageThread } from "@/components/chat/message-thread";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { streamMessage } from "@/shared/api/chat";
import { getConversation } from "@/shared/api/conversations";
import { listDocuments } from "@/shared/api/documents";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useSettingsModelsQuery } from "@/shared/hooks/use-settings-models-query";
import { queryKeys } from "@/shared/query/keys";
import { useI18n } from "@/shared/i18n/use-language";
import type { ChatReply, ChatToolCallSummary, Citation } from "@/shared/api/types";

const CitationsDrawer = dynamic(
  () =>
    import("@/components/chat/citations-drawer").then((module) => ({
      default: module.CitationsDrawer,
    })),
  { ssr: false, loading: () => null },
);

export function ChatView({ conversationId }: { conversationId: string }) {
  const queryClient = useQueryClient();
  const { t } = useI18n();
  const workspaceId = useActiveWorkspaceId();
  const [latestCitations, setLatestCitations] = useState<Citation[]>([]);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [toolCalls, setToolCalls] = useState<ChatToolCallSummary[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const { data: conversation, isLoading } = useQuery({
    queryKey: queryKeys.conversations.detail(conversationId),
    queryFn: () => getConversation(conversationId),
  });

  const { data: models = [] } = useSettingsModelsQuery();

  const { data: documents = [] } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });

  async function handleSubmit(payload: ComposerSubmitPayload) {
    if (!conversation) return;
    setIsStreaming(true);
    setStreamingMessage("");
    setLatestCitations([]);
    setToolCalls([]);

    try {
      await streamMessage(
        {
          conversation_id: conversationId,
          content: payload.content,
          use_retrieval: payload.useRetrieval,
          workspace_id: workspaceId ?? conversation.workspace_id ?? undefined,
          document_ids: payload.documentIds,
          top_k: payload.topK,
          enabled_tool_names: payload.enabledToolNames ?? conversation.effective_tool_names,
        },
        {
          onEvent: (event, data) => {
            if (event === "content_delta") {
              setStreamingMessage((current) => current + String(data.delta ?? ""));
              return;
            }
            if (event === "citations") {
              setLatestCitations((data.citations as Citation[]) ?? []);
              return;
            }
            if (event === "tool_call_start" || event === "tool_call_end") {
              const toolCall = data as unknown as ChatToolCallSummary;
              setToolCalls((current) => {
                const next = current.filter((item) => item.tool_name !== toolCall.tool_name);
                return [...next, toolCall];
              });
              return;
            }
            if (event === "message_complete") {
              const complete = data as unknown as ChatReply & { citations?: Citation[] };
              setLatestCitations((complete.citations as Citation[]) ?? []);
              queryClient.invalidateQueries({
                queryKey: queryKeys.conversations.detail(conversationId),
              });
              queryClient.invalidateQueries({ queryKey: queryKeys.conversations.list() });
              setStreamingMessage("");
              return;
            }
            if (event === "error") {
              toast.error(String(data.message ?? t.chatView.streamingFailed));
            }
          },
        },
      );
    } catch (error) {
      toast.error(`${t.chatView.sendFailedPrefix} ${(error as Error).message}`);
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex h-full flex-col bg-[radial-gradient(circle_at_top,_rgba(27,94,80,0.12),_transparent_45%),linear-gradient(180deg,rgba(250,246,239,0.96),rgba(255,255,255,1))]">
      <div className="border-b bg-background/70 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">{conversation?.title ?? t.chatView.conversationFallback}</h2>
              <p className="text-sm text-muted-foreground">
                {conversation
                  ? `${conversation.effective_agent_name ?? t.chatView.workspaceRuntime} · ${conversation.provider} · ${conversation.model}`
                  : ""}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {toolCalls.length > 0 && (
                <div className="flex flex-wrap items-center gap-2">
                  {toolCalls.map((toolCall) => (
                    <Badge key={toolCall.tool_name} variant="outline" className="gap-1 font-mono">
                      <Wrench className="h-3 w-3" />
                      {toolCall.tool_name}
                      <span className="text-[11px] text-muted-foreground">
                        {toolCall.latency_ms}ms
                      </span>
                    </Badge>
                  ))}
                </div>
              )}
              <CitationsDrawer citations={latestCitations} />
            </div>
          </div>
          {conversation && (
            <ChatRuntimeControls
              conversation={conversation}
              models={models}
              onConversationChange={(updated) => {
                queryClient.setQueryData(queryKeys.conversations.detail(conversationId), updated);
                queryClient.invalidateQueries({ queryKey: queryKeys.conversations.list() });
              }}
            />
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="mx-auto max-w-5xl">
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-16 w-2/3" />
              <Skeleton className="h-16 w-1/2" />
            </div>
          )}
          {!isLoading && conversation?.messages.length === 0 && (
            <div className="rounded-3xl border border-dashed bg-background/80 p-10 text-center shadow-sm">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Bot className="h-5 w-5 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">{t.chatView.emptyTitle}</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                {t.chatView.emptyDescription}
              </p>
            </div>
          )}
          {conversation && (
            <MessageThread
              messages={conversation.messages}
              isPending={isStreaming}
              streamingMessage={streamingMessage}
            />
          )}
        </div>
      </div>

      <MessageComposer
        onSubmit={handleSubmit}
        disabled={isStreaming}
        documents={documents}
        toolToggles={(conversation?.effective_tool_names ?? []).map((toolName) => ({
          tool_name: toolName,
          enabled: true,
        }))}
      />
    </div>
  );
}
