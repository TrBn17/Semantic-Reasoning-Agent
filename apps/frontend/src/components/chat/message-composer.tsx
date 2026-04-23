"use client";

import { ChevronDown, Send, SlidersHorizontal } from "lucide-react";
import { useMemo, useState, type FormEvent, type KeyboardEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import type { DocumentResponse } from "@/shared/api/types";
import { useI18n } from "@/shared/i18n/use-language";

export interface ComposerSubmitPayload {
  content: string;
  useRetrieval: boolean;
  topK: number;
  documentIds: string[];
  enabledToolNames?: string[] | null;
}

interface ToolToggle {
  tool_name: string;
  label?: string;
  enabled: boolean;
  locked?: boolean;
  reason?: string;
}

export function MessageComposer({
  onSubmit,
  disabled,
  documents = [],
  toolToggles = [],
}: {
  onSubmit: (payload: ComposerSubmitPayload) => void;
  disabled?: boolean;
  documents?: DocumentResponse[];
  toolToggles?: ToolToggle[];
}) {
  const { t } = useI18n();
  const [useRetrieval, setUseRetrieval] = useState(false);
  const [topK, setTopK] = useState(3);
  const [content, setContent] = useState("");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [documentIds, setDocumentIds] = useState<string[]>([]);
  const [sessionTools, setSessionTools] = useState<Record<string, boolean>>({});

  const indexedDocuments = useMemo(
    () => documents.filter((document) => document.status === "indexed"),
    [documents],
  );

  function submit(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || disabled) return;
    onSubmit({
      content: trimmed,
      useRetrieval,
      topK,
      documentIds,
      enabledToolNames: toolToggles
        .filter((tool) => (sessionTools[tool.tool_name] ?? tool.enabled))
        .map((tool) => tool.tool_name),
    });
    setContent("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  function toggleDocument(documentId: string) {
    setDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((item) => item !== documentId)
        : [...current, documentId],
    );
  }

  return (
    <form onSubmit={submit} className="border-t bg-background p-4">
      <div className="mx-auto flex max-w-5xl flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant={useRetrieval ? "info" : "outline"}>
              {useRetrieval ? t.chat.retrievalOn : t.chat.retrievalOff}
            </Badge>
            {documentIds.length > 0 && (
              <Badge variant="outline">{t.chat.scopedDocs.replace("{count}", String(documentIds.length))}</Badge>
            )}
            {toolToggles
              .filter((tool) => sessionTools[tool.tool_name] ?? tool.enabled)
              .slice(0, 3)
              .map((tool) => (
                <Badge key={tool.tool_name} variant="outline" className="font-mono text-[11px]">
                  {tool.label ?? tool.tool_name}
                </Badge>
              ))}
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setAdvancedOpen((current) => !current)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            {t.chat.advanced}
            <ChevronDown className={`h-4 w-4 transition ${advancedOpen ? "rotate-180" : ""}`} />
          </Button>
        </div>

        {advancedOpen && (
          <div className="grid gap-4 rounded-2xl border bg-muted/20 p-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="space-y-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-input"
                  checked={useRetrieval}
                  onChange={(event) => setUseRetrieval(event.target.checked)}
                />
                {t.chat.useRetrieval}
              </label>
              {useRetrieval && (
                <>
                  <div className="flex items-center gap-2">
                    <Label htmlFor="top-k">{t.chat.topK}</Label>
                    <Input
                      id="top-k"
                      type="number"
                      min={1}
                      max={20}
                      value={topK}
                      onChange={(event) => setTopK(Number(event.target.value) || 3)}
                      className="h-9 w-20"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>{t.chat.documentIds}</Label>
                    <ScrollArea className="h-40 rounded-xl border bg-background">
                      <div className="space-y-1 p-2">
                        {indexedDocuments.map((document) => {
                          const selected = documentIds.includes(document.id);
                          return (
                            <button
                              key={document.id}
                              type="button"
                              onClick={() => toggleDocument(document.id)}
                              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition ${
                                selected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                              }`}
                            >
                              <span className="truncate">{document.title}</span>
                              <span className="text-[11px] text-muted-foreground">
                                {selected ? t.chat.scoped : t.chat.allWorkspace}
                              </span>
                            </button>
                          );
                        })}
                        {indexedDocuments.length === 0 && (
                          <div className="px-3 py-5 text-sm text-muted-foreground">
                            {t.chat.noIndexedDocuments}
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  </div>
                </>
              )}
            </div>

            <div className="space-y-3">
              <Label>{t.chat.sessionToolVisibility}</Label>
              <div className="space-y-2 rounded-xl border bg-background p-3">
                {toolToggles.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    Tool controls come from the selected agent profile.
                  </p>
                )}
                {toolToggles.map((tool) => {
                  const enabled = sessionTools[tool.tool_name] ?? tool.enabled;
                  return (
                    <label key={tool.tool_name} className="flex items-start justify-between gap-3 text-sm">
                      <div>
                        <div className="text-xs font-medium">{tool.label ?? tool.tool_name}</div>
                        <div className="font-mono text-[10px] text-muted-foreground">{tool.tool_name}</div>
                        {tool.reason && (
                          <div className="text-xs text-muted-foreground">{tool.reason}</div>
                        )}
                      </div>
                      <input
                        type="checkbox"
                        checked={enabled}
                        disabled={tool.locked}
                        onChange={(event) =>
                          setSessionTools((current) => ({
                            ...current,
                            [tool.tool_name]: event.target.checked,
                          }))
                        }
                      />
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        <div className="flex items-end gap-3">
          <Textarea
            value={content}
            onChange={(event) => setContent(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t.chat.noContentHint}
            className="min-h-[92px] flex-1 rounded-2xl border-0 bg-muted/30 px-4 py-3 shadow-inner"
            disabled={disabled}
          />
          <Button type="submit" disabled={disabled || !content.trim()} size="lg" className="h-12 rounded-xl px-5">
            <Send className="h-4 w-4" />
            {t.chat.send}
          </Button>
        </div>
      </div>
    </form>
  );
}
