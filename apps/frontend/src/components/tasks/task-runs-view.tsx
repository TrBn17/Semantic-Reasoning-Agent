"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { resolveTask } from "@/shared/api/tasks";
import type { TaskResolveResponse } from "@/shared/api/types";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useI18n } from "@/shared/i18n/use-language";

export function TaskRunsView() {
  const { t } = useI18n();
  const workspaceId = useActiveWorkspaceId();
  const [content, setContent] = useState("");
  const [provider, setProvider] = useState("");
  const [model, setModel] = useState("");
  const [result, setResult] = useState<TaskResolveResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      resolveTask({
        content: content.trim(),
        workspace_id: workspaceId ?? undefined,
        provider: provider || undefined,
        model: model || undefined,
      }),
    onSuccess: (data) => {
      setResult(data);
      toast.success(t.tasksUi.taskResolved);
    },
    onError: (error) => toast.error(`${t.tasksUi.taskFailedPrefix} ${(error as Error).message}`),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.tasksUi.runTask}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>{t.tasksUi.content}</Label>
            <Textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder={t.tasksUi.contentPlaceholder}
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label>{t.tasksUi.providerOptional}</Label>
              <Input value={provider} onChange={(event) => setProvider(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>{t.tasksUi.modelOptional}</Label>
              <Input value={model} onChange={(event) => setModel(event.target.value)} />
            </div>
          </div>
          <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !content.trim()}>
            {mutation.isPending ? t.tasksUi.resolving : t.tasksUi.resolveTask}
          </Button>
        </CardContent>
      </Card>

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t.tasksUi.result}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-xs text-muted-foreground">
              task_id: <span className="font-mono">{result.task_id}</span> · {t.tasksUi.outputPrefix}:{" "}
              {result.output_type}
            </div>
            <p className="whitespace-pre-wrap text-sm">{result.content}</p>
            <pre className="overflow-auto rounded-md bg-muted/40 p-3 text-xs">
              {JSON.stringify(
                { citations: result.citations, evidence: result.evidence, trace: result.trace },
                null,
                2,
              )}
            </pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
