"use client";

import { Send } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export interface ComposerSubmitPayload {
  content: string;
  useRetrieval: boolean;
  topK: number;
  documentIds: string[];
}

export function MessageComposer({
  onSubmit,
  disabled,
}: {
  onSubmit: (payload: ComposerSubmitPayload) => void;
  disabled?: boolean;
}) {
  const [useRetrieval, setUseRetrieval] = useState(false);
  const [topK, setTopK] = useState(3);
  const [content, setContent] = useState("");
  const [documentIds, setDocumentIds] = useState("");

  function submit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || disabled) return;
    onSubmit({
      content: trimmed,
      useRetrieval,
      topK,
      documentIds: documentIds
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    });
    setContent("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <form
      onSubmit={submit}
      className="space-y-2 border-t bg-background p-4"
    >
      <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-input"
            checked={useRetrieval}
            onChange={(e) => setUseRetrieval(e.target.checked)}
          />
          Use retrieval (RAG)
        </label>
        {useRetrieval && (
          <>
            <div className="flex items-center gap-2">
              <Label htmlFor="top-k">top_k</Label>
              <Input
                id="top-k"
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value) || 3)}
                className="h-7 w-16"
              />
            </div>
            <div className="flex flex-1 items-center gap-2">
              <Label htmlFor="doc-ids">document_ids (comma sep)</Label>
              <Input
                id="doc-ids"
                value={documentIds}
                onChange={(e) => setDocumentIds(e.target.value)}
                placeholder="optional"
                className="h-7 flex-1"
              />
            </div>
          </>
        )}
      </div>
      <div className="flex items-end gap-2">
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message. Shift+Enter for newline."
          className="min-h-[72px] flex-1"
          disabled={disabled}
        />
        <Button type="submit" disabled={disabled || !content.trim()} size="lg">
          <Send className="h-4 w-4" />
          Send
        </Button>
      </div>
    </form>
  );
}
