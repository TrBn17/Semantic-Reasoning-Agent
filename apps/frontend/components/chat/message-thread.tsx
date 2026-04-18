"use client";

import { Bot, User } from "lucide-react";
import { cn, formatDateTime } from "@/lib/utils";
import type { Message } from "@/lib/api/types";

export function MessageThread({
  messages,
  isPending,
}: {
  messages: Message[];
  isPending?: boolean;
}) {
  return (
    <div className="space-y-6">
      {messages.map((m) => (
        <MessageRow key={m.id} message={m} />
      ))}
      {isPending && (
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

function MessageRow({ message }: { message: Message }) {
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
          <span>·</span>
          <span>{formatDateTime(message.created_at)}</span>
        </div>
        <div className="whitespace-pre-wrap break-words rounded-md bg-card px-3 py-2 text-sm leading-6 shadow-sm ring-1 ring-border">
          {message.content}
        </div>
      </div>
    </div>
  );
}
