"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
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
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listDocuments } from "@/lib/api/documents";
import { extractAndPublish } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function NewBuildDialog() {
  const { t } = useI18n();
  const x = t.knowledgeGraph.extractDialog;
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [documentIds, setDocumentIds] = useState<string[]>([]);

  const { data: documents } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });

  const mutation = useMutation({
    mutationFn: async () => {
      if (documentIds.length === 0) throw new Error(x.pickError);
      const queued = await Promise.allSettled(
        documentIds.map((document_id) =>
          extractAndPublish({
            document_id,
            workspace_id: workspaceId ?? undefined,
          }),
        ),
      );

      let successCount = 0;
      const failures: string[] = [];
      queued.forEach((result) => {
        if (result.status === "fulfilled") {
          successCount += 1;
          return;
        }
        failures.push(result.reason instanceof Error ? result.reason.message : t.common.unknown);
      });

      return { successCount, failures };
    },
    onSuccess: ({ successCount, failures }) => {
      if (successCount > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      }

      if (successCount > 0 && failures.length === 0) {
        toast.success(x.toastPublished.replace("{n}", String(successCount)));
        setOpen(false);
      } else if (successCount > 0) {
        toast.warning(
          x.toastPartial
            .replace("{ok}", String(successCount))
            .replace("{fail}", String(failures.length))
            .replace("{detail}", failures.slice(0, 2).join(" | ")),
        );
      } else {
        toast.error(
          x.toastFailed.replace("{detail}", failures.slice(0, 2).join(" | ")),
        );
      }

      setDocumentIds([]);
    },
    onError: (err) =>
      toast.error(`${x.toastError} ${(err as Error).message}`),
  });

  const indexed = (documents ?? []).filter((d) => d.status === "indexed");
  const toggleSelection = (documentId: string) => {
    setDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          {x.trigger}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{x.title}</DialogTitle>
          <DialogDescription>{x.description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label>{x.documentsLabel}</Label>
          <ScrollArea className="h-56 rounded-md border">
            <div className="space-y-1 p-2">
              {indexed.map((d) => {
                const checked = documentIds.includes(d.id);
                return (
                  <button
                    key={d.id}
                    type="button"
                    className={`flex w-full items-center justify-between rounded px-2 py-1.5 text-left text-sm transition ${
                      checked
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-muted/60"
                    }`}
                    onClick={() => toggleSelection(d.id)}
                  >
                    <span className="truncate">{d.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {checked ? x.selected : x.unselected}
                    </span>
                  </button>
                );
              })}
              {indexed.length === 0 && (
                <div className="p-2 text-xs text-muted-foreground">{x.noIndexedDocs}</div>
              )}
            </div>
          </ScrollArea>
          {documentIds.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {documentIds.length} {x.nSelected}
            </p>
          )}
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              {x.cancel}
            </Button>
          </DialogClose>
          <Button
            onClick={() => mutation.mutate()}
            disabled={documentIds.length === 0 || mutation.isPending}
          >
            {mutation.isPending ? x.running : x.run}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
