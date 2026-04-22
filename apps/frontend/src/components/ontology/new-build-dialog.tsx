"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { toast } from "sonner";
import { ModelCombobox } from "@/components/agents/model-combobox";
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
import { createBuild } from "@/shared/api/ontology";
import { useActiveWorkspaceId } from "@/shared/hooks/use-active-workspace-id";
import { useSettingsModelsQuery } from "@/shared/hooks/use-settings-models-query";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { parseModelValue } from "@/shared/utils/model-value";
import { rankItems } from "@/shared/utils/fuzzy";

export function NewBuildDialog() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useActiveWorkspaceId();
  const [open, setOpen] = useState(false);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [modelSelection, setModelSelection] = useState<string>("");

  const { data: documents } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });
  const { data: models = [] } = useSettingsModelsQuery();

  const indexedDocuments = useMemo(
    () => {
      const indexed = (documents ?? []).filter((document) => document.status === "indexed");
      if (!search.trim()) return indexed;
      return rankItems(indexed, search, (document) => [
        document.title,
        document.filename,
        document.document_type,
        document.source_url,
        document.tags.join(" "),
      ]).map(({ item }) => item);
    },
    [documents, search],
  );
  const ontologyModels = useMemo(
    () =>
      models
        .sort((a, b) => {
          if (a.supports_structured_output !== b.supports_structured_output) {
            return a.supports_structured_output ? -1 : 1;
          }
          if (a.ready !== b.ready) return a.ready ? -1 : 1;
          return a.label.localeCompare(b.label);
        }),
    [models],
  );

  const mutation = useMutation({
    mutationFn: async () => {
      if (!documentId) throw new Error(t.ontologyUi.pickDocument);
      const selection = parseModelValue(modelSelection);
      if (!selection) throw new Error(t.ontologyUi.pickExtractionModel);
      return createBuild({
        document_id: documentId,
        workspace_id: workspaceId ?? undefined,
        extraction_provider: selection.provider,
        extraction_model: selection.model,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      toast.success(t.ontologyUi.buildQueued);
      setOpen(false);
      setDocumentId(null);
      setModelSelection("");
    },
    onError: (err) => toast.error(`${t.ontologyUi.buildFailedPrefix} ${(err as Error).message}`),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="rounded-xl">
          <Plus className="h-4 w-4" />
          {t.ontologyUi.newBuild}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl" closeLabel={t.common.accessibility.closeDialog}>
        <DialogHeader>
          <DialogTitle>{t.ontologyUi.runOntologyExtraction}</DialogTitle>
          <DialogDescription>{t.ontologyUi.runOntologyExtractionDescription}</DialogDescription>
        </DialogHeader>

        <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-3">
            <Label>{t.ontologyUi.indexedDocument}</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={t.ontologyUi.filterDocuments}
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
                    {t.ontologyUi.noIndexedDocumentsMatch}
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>

          <div className="min-w-0 space-y-3 overflow-hidden">
            <Label>{t.ontologyUi.extractionModel}</Label>
            <div className="rounded-2xl border bg-muted/20 p-4">
              <ModelCombobox
                models={ontologyModels}
                value={modelSelection}
                onChange={setModelSelection}
                collapseOnSelect
                labels={{
                  providerPlaceholder: t.agentsSettings.picker.providerPlaceholder,
                  allProviders: t.agentsSettings.picker.allProviders,
                  searchModelPlaceholder: t.agentsSettings.picker.searchModelPlaceholder,
                  selectModelPlaceholder: t.ontologyUi.pickExtractionModel,
                  noModelMatch: t.agentsSettings.picker.noModelMatch,
                  assignmentUnavailable: t.agentsSettings.picker.assignmentUnavailable,
                  readyBadge: t.agentsSettings.picker.readyBadge,
                  blockedBadge: t.agentsSettings.picker.blockedBadge,
                  capabilityStreaming: t.agentsSettings.picker.capabilityStreaming,
                  capabilityStructured: t.agentsSettings.picker.capabilityStructured,
                }}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              {t.common.cancel}
            </Button>
          </DialogClose>
          <Button onClick={() => mutation.mutate()} disabled={!documentId || !modelSelection || mutation.isPending}>
            {mutation.isPending ? t.ontologyUi.queueing : t.ontologyUi.startBuild}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
