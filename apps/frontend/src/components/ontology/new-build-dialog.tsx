"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, Plus, Search } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { listDocuments } from "@/shared/api/documents";
import { listModels } from "@/shared/api/models";
import { createBuild } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";

function composeValue(provider: string, model: string) {
  return `${provider}::${model}`;
}

export function NewBuildDialog() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [open, setOpen] = useState(false);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [modelSelection, setModelSelection] = useState<string>("");

  const { data: documents } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });
  const { data: models = [] } = useQuery({
    queryKey: [...queryKeys.models, workspaceId ?? null],
    queryFn: () => listModels(workspaceId),
  });

  const indexedDocuments = useMemo(
    () =>
      (documents ?? [])
        .filter((document) => document.status === "indexed")
        .filter((document) =>
          document.title.toLowerCase().includes(search.trim().toLowerCase()),
        ),
    [documents, search],
  );
  const ontologyModels = useMemo(
    () =>
      models
        .filter((model) => model.supports_structured_output || model.ready)
        .sort((a, b) => {
          if (a.ready !== b.ready) return a.ready ? -1 : 1;
          return a.label.localeCompare(b.label);
        }),
    [models],
  );

  const mutation = useMutation({
    mutationFn: async () => {
      if (!documentId) throw new Error("Pick a document");
      const selection = modelSelection.split("::");
      return createBuild({
        document_id: documentId,
        workspace_id: workspaceId ?? undefined,
        provider: selection[0] || undefined,
        model: selection[1] || undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      toast.success("Ontology build queued");
      setOpen(false);
      setDocumentId(null);
      setModelSelection("");
    },
    onError: (err) => toast.error(`Build failed: ${(err as Error).message}`),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="rounded-xl">
          <Plus className="h-4 w-4" />
          New build
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Run ontology extraction</DialogTitle>
          <DialogDescription>
            Choose the indexed document and the extraction model, then queue a reviewable build.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-3">
            <Label>Indexed document</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filter documents"
                className="pl-9"
              />
            </div>
            <ScrollArea className="h-72 rounded-xl border">
              <div className="space-y-1 p-2">
                {indexedDocuments.map((document) => {
                  const selected = documentId === document.id;
                  return (
                    <button
                      key={document.id}
                      type="button"
                      onClick={() => setDocumentId(document.id)}
                      className={`w-full rounded-xl px-3 py-3 text-left transition ${
                        selected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                      }`}
                    >
                      <div className="font-medium">{document.title}</div>
                      <div className="text-xs text-muted-foreground">{document.filename}</div>
                    </button>
                  );
                })}
                {indexedDocuments.length === 0 && (
                  <div className="px-3 py-6 text-sm text-muted-foreground">
                    No indexed documents match that filter.
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          <div className="space-y-3">
            <Label>Extraction model</Label>
            <div className="rounded-2xl border bg-muted/20 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium">
                <BrainCircuit className="h-4 w-4" />
                Model override
              </div>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setModelSelection("")}
                  className={`w-full rounded-xl border px-3 py-2 text-left text-sm ${
                    modelSelection === "" ? "border-primary bg-primary/5" : "bg-background"
                  }`}
                >
                  Workspace default
                </button>
                <ScrollArea className="h-56 rounded-xl border bg-background">
                  <div className="space-y-1 p-2">
                    {ontologyModels.map((model) => {
                      const value = composeValue(model.provider, model.model);
                      const selected = modelSelection === value;
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setModelSelection(value)}
                          className={`w-full rounded-xl px-3 py-3 text-left transition ${
                            selected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                          }`}
                        >
                          <div className="font-medium">{model.label}</div>
                          <div className="text-xs text-muted-foreground">
                            {model.provider} · {model.ready ? "ready" : model.reason}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </ScrollArea>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              Cancel
            </Button>
          </DialogClose>
          <Button onClick={() => mutation.mutate()} disabled={!documentId || mutation.isPending}>
            {mutation.isPending ? "Queueing..." : "Start build"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
