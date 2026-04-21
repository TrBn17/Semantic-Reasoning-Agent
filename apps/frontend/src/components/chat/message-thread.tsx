"use client";

import { Bot, User } from "lucide-react";
import { cn, formatDateTime } from "@/shared/utils";
import type { Message } from "@/shared/api/types";

export function MessageThread({
  messages,
  isPending,
  streamingMessage,
}: {
  messages: Message[];
  isPending?: boolean;
  streamingMessage?: string;
}) {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <MessageRow key={message.id} message={message} />
      ))}
      {streamingMessage && (
        <MessageRow
          pending
          message={{
            id: "streaming-assistant",
            role: "assistant",
            content: streamingMessage,
            created_at: new Date().toISOString(),
          }}
        />
      )}
      {isPending && !streamingMessage && (
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
            <Bot className="h-4 w-4" />
          </div>
          <div className="flex-1 space-y-2">
            <div className="text-xs text-muted-foreground">Assistant</div>
            <div className="h-2 w-24 animate-pulse rounded bg-muted" />
            <div className="h-2 w-48 animate-pulse rounded bg-muted" />
          </div>
        </div>
      )}
    </div>
  );
}

function MessageRow({
  message,
  pending = false,
}: {
  message: Message;
  pending?: boolean;
}) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div className="flex items-start gap-3">
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-primary text-primary-foreground"
            : isSystem
              ? "bg-amber-500/20 text-amber-700"
              : "bg-muted text-muted-foreground",
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>
      <div className="flex-1 space-y-1">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium capitalize">{message.role}</span>
          <span>•</span>
          <span>{pending ? "Streaming..." : formatDateTime(message.created_at)}</span>
        </div>
        <div className="whitespace-pre-wrap break-words rounded-2xl bg-card px-4 py-3 text-sm leading-6 shadow-sm ring-1 ring-border">
          {message.content}
          {pending && (
            <span className="ml-1 inline-block h-4 w-2 animate-pulse rounded bg-primary/40 align-middle" />
          )}
        </div>
      </div>
    </div>
  );
}
