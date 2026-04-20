"use client";

import { useMutation } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { invokeTool } from "@/lib/api/tools";
import type {
  Evidence,
  StandardToolInput,
  StandardToolOutput,
  ToolSpec,
  ToolStatus,
} from "@/lib/api/types";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function ToolInvokeDialog({ tool }: { tool: ToolSpec }) {
  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [taskType, setTaskType] = useState(t.tools.invokeDialog.defaults.taskType);
  const [workspaceInput, setWorkspaceInput] = useState("");
  const [argumentsText, setArgumentsText] = useState(() =>
    defaultArgumentsFor(tool),
  );
  const [result, setResult] = useState<StandardToolOutput | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const args = parseJson(argumentsText, t);
      const resolvedWorkspaceId = (workspaceInput || workspaceId || "").trim();
      if (!resolvedWorkspaceId) {
        throw new Error(t.common.workspaceRequired);
      }
      const payload: StandardToolInput = {
        call_id: crypto.randomUUID(),
        tool_name: tool.tool_name,
        workspace_id: resolvedWorkspaceId,
        task_id: crypto.randomUUID(),
        task_type: taskType.trim() || t.tools.invokeDialog.defaults.taskType,
        arguments: args,
      };
      return invokeTool(tool.tool_name, payload);
    },
    onSuccess: (output) => {
      setResult(output);
      if (output.status === "success") {
        toast.success(
          `${tool.tool_name} ${t.tools.invokeDialog.status.success.toLowerCase()} — ${output.evidence.length} ${t.common.evidence}, ${output.latency_ms}ms`,
        );
      } else if (output.status === "partial") {
        toast.warning(
          `${tool.tool_name} ${t.tools.invokeDialog.status.partial.toLowerCase()} — ${t.tools.invokeDialog.results.hints}: ${output.next_action_hints.join(", ") || t.common.none}`,
        );
      } else {
        toast.error(
          `${tool.tool_name} ${t.tools.invokeDialog.status.failed.toLowerCase()} — ${output.error_code ?? t.common.unknown}: ${output.error_message ?? ""}`,
        );
      }
    },
    onError: (err) => {
      setResult(null);
      toast.error(`${t.common.invokeFailed} ${(err as Error).message}`);
    },
  });

  const handleSubmit = () => {
    setParseError(null);
    try {
      parseJson(argumentsText, t);
    } catch (err) {
      setParseError((err as Error).message);
      return;
    }
    mutation.mutate();
  };

  const onOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setResult(null);
      setParseError(null);
      mutation.reset();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline" className="gap-1.5 rounded-full">
          <Play className="h-3.5 w-3.5" />
          {t.common.invoke}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl rounded-2xl">
        <DialogHeader>
          <DialogTitle className="font-mono text-base">
            {tool.tool_name}
          </DialogTitle>
          <DialogDescription className="max-w-2xl">
            {tool.description}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 rounded-2xl border bg-muted/20 p-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="workspace">{t.common.workspaceId}</Label>
            <Input
              id="workspace"
              value={workspaceInput}
              placeholder={workspaceId ?? t.tools.invokeDialog.defaults.workspacePlaceholder}
              onChange={(e) => setWorkspaceInput(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="task-type">{t.common.taskType}</Label>
            <Input
              id="task-type"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-1.5 rounded-2xl border bg-muted/10 p-4">
          <div className="flex items-baseline justify-between">
            <Label htmlFor="arguments">{t.tools.invokeDialog.arguments}</Label>
            <SchemaHint tool={tool} />
          </div>
          <Textarea
            id="arguments"
            rows={8}
            value={argumentsText}
            onChange={(e) => setArgumentsText(e.target.value)}
            className="font-mono text-xs"
          />
          {parseError && (
            <p className="text-xs text-destructive">{t.tools.invokeDialog.parseErrorPrefix} {parseError}</p>
          )}
        </div>

        {result && <InvokeResult result={result} />}

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              {t.tools.invokeDialog.close}
            </Button>
          </DialogClose>
          <Button onClick={handleSubmit} disabled={mutation.isPending} className="rounded-full">
            {mutation.isPending ? t.tools.invokeDialog.invoking : t.tools.invokeDialog.invoke}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SchemaHint({ tool }: { tool: ToolSpec }) {
  const { t } = useI18n();
  const required = useMemo(() => {
    const req = tool.input_schema?.required;
    return Array.isArray(req) ? (req as string[]) : [];
  }, [tool.input_schema]);

  if (required.length === 0) {
    return (
      <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
        {t.tools.invokeDialog.schemaPrefix} {tool.input_schema_ref || tool.output_schema_ref}
      </span>
    );
  }
  return (
    <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
      {t.tools.invokeDialog.requiredPrefix} {required.join(", ")}
    </span>
  );
}

function InvokeResult({ result }: { result: StandardToolOutput }) {
  const { t } = useI18n();

  return (
    <div className="space-y-3 rounded-2xl border bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <StatusBadge status={result.status} />
          <span className="font-mono text-xs text-muted-foreground">
            {result.latency_ms}ms
          </span>
          {result.meta.trace_id && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {t.tools.invokeDialog.results.trace} {result.meta.trace_id.slice(0, 8)}
            </span>
          )}
        </div>
        <span className="font-mono text-xs">
          {result.evidence.length} {t.common.evidence} · {result.artifacts.length} {t.common.artifacts}
        </span>
      </div>

      {result.error_code && (
        <div className="rounded border border-destructive/30 bg-destructive/10 p-2 text-xs">
          <div className="font-mono font-semibold text-destructive">
            {result.error_code}
          </div>
          {result.error_message && (
            <div className="text-destructive/90">{result.error_message}</div>
          )}
        </div>
      )}

      {result.next_action_hints.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 text-xs">
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{t.tools.invokeDialog.results.hints}</span>
          {result.next_action_hints.map((hint) => (
            <Badge key={hint} variant="info" className="rounded-full font-mono text-[10px]">
              {hint}
            </Badge>
          ))}
        </div>
      )}

      {result.evidence.length > 0 && (
        <ScrollArea className="max-h-56 rounded-2xl border bg-background">
          <div className="divide-y">
            {result.evidence.map((ev) => (
              <EvidenceRow key={ev.evidence_id} evidence={ev} />
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  return (
    <div className="space-y-1.5 p-3 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="rounded-full font-mono text-[10px]">
            {evidence.source_type}
          </Badge>
          <span className="font-medium text-foreground">{evidence.title}</span>
        </div>
        <span className="text-muted-foreground">
          {evidence.citation_anchor.anchor_type} · {evidence.citation_anchor.label}
          {evidence.score > 0 ? ` · ${evidence.score.toFixed(3)}` : ""}
        </span>
      </div>
      <p className="line-clamp-2 leading-5 text-muted-foreground">{evidence.content}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: ToolStatus }) {
  const { t } = useI18n();
  const variant =
    status === "success" ? "success" : status === "partial" ? "warning" : "destructive";
  const label =
    status === "success"
      ? t.tools.invokeDialog.status.success
      : status === "partial"
        ? t.tools.invokeDialog.status.partial
        : t.tools.invokeDialog.status.failed;
  return (
    <Badge variant={variant} className="capitalize">
      {label}
    </Badge>
  );
}

function defaultArgumentsFor(tool: ToolSpec): string {
  if (tool.tool_name === "retrieval.internal") {
    return JSON.stringify({ query: "", top_k: 5 }, null, 2);
  }
  if (tool.tool_name === "ontology.lookup") {
    return JSON.stringify({ mode: "published_graph" }, null, 2);
  }
  return "{}";
}

function parseJson(text: string, t: ReturnType<typeof useI18n>["t"]): Record<string, unknown> {
  if (!text.trim()) return {};
  const parsed = JSON.parse(text);
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw new Error(t.tools.invokeDialog.argumentsObjectError);
  }
  return parsed as Record<string, unknown>;
}
