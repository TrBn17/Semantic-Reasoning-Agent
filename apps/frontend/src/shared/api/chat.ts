import { apiFetch } from "@/shared/api/client";
import { getApiBaseUrl } from "@/shared/api/api-base";
import type { ChatReply, ChatStreamEventType, SendMessageRequest } from "@/shared/api/types";

export function sendMessage(payload: SendMessageRequest): Promise<ChatReply> {
  return apiFetch<ChatReply>("/chat/messages", {
    method: "POST",
    body: payload,
  });
}

export async function streamMessage(
  payload: SendMessageRequest,
  handlers: {
    onEvent?: (event: ChatStreamEventType, data: Record<string, unknown>) => void;
  } = {},
): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/chat/messages/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok || !response.body) {
    const message = await response.text().catch(() => "Streaming request failed");
    throw new Error(message || `Streaming request failed with ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const rawEvent = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");

      if (!rawEvent) {
        continue;
      }

      const typeLine = rawEvent
        .split("\n")
        .find((line) => line.startsWith("event:"));
      const dataLine = rawEvent
        .split("\n")
        .find((line) => line.startsWith("data:"));

      const event = typeLine?.replace("event:", "").trim() as ChatStreamEventType | undefined;
      const rawData = dataLine?.replace("data:", "").trim();
      if (!event || !rawData) {
        continue;
      }

      const data = JSON.parse(rawData) as Record<string, unknown>;
      handlers.onEvent?.(event, data);
    }
  }
}
