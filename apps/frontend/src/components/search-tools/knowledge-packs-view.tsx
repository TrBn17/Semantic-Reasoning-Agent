"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  createKnowledgePack,
  deleteKnowledgePack,
  listKnowledgePackDocuments,
  listKnowledgePacks,
} from "@/shared/api/knowledge-packs";
import { queryKeys } from "@/shared/query/keys";
import { useI18n } from "@/shared/i18n/use-language";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { notify } from "@/shared/ui/notify";

export function KnowledgePacksView() {
  const normalizeError = (error: Error): string => {
    const message = error.message || "";
    if (message.toLowerCase().includes("out-of-scope document ids")) {
      return t.documents.toasts.outOfScopeDocument;
    }
    return message;
  };

  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const queryClient = useQueryClient();
  const [newKnowledgeName, setNewKnowledgeName] = useState("");
  const [selectedPackId, setSelectedPackId] = useState<string>("");

  const { data: packs } = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
  });
  const { data: packDocuments } = useQuery({
    queryKey: ["knowledge-packs", selectedPackId, "documents"],
    queryFn: () => listKnowledgePackDocuments(selectedPackId),
    enabled: Boolean(selectedPackId),
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      if (!workspaceId) throw new Error(t.knowledgePacksPage.toasts.workspaceRequired);
      const name = newKnowledgeName.trim();
      if (!name) throw new Error(t.knowledgePacksPage.toasts.emptyName);
      return createKnowledgePack({
        workspace_id: workspaceId,
        name,
      });
    },
    onSuccess: (pack) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgePacks.all });
      setNewKnowledgeName("");
      setSelectedPackId(pack.id);
      notify.success(t.knowledgePacksPage.toasts.created);
    },
    onError: (error) => notify.error(normalizeError(error as Error), t.common.error),
  });

  const deleteMutation = useMutation({
    mutationFn: async (packId: string) => {
      if (!packId) throw new Error(t.knowledgePacksPage.toasts.selectPackToDelete);
      await deleteKnowledgePack(packId);
    },
    onSuccess: (_, packId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgePacks.all });
      if (packId === selectedPackId) {
        setSelectedPackId("");
      }
      notify.success(t.knowledgePacksPage.toasts.deleted);
    },
    onError: (error) => notify.error(normalizeError(error as Error), t.common.error),
  });

  const selectedPackName = useMemo(
    () => (packs ?? []).find((pack) => pack.id === selectedPackId)?.name ?? "",
    [packs, selectedPackId],
  );

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{t.knowledgePacksPage.title}</h1>
      </div>
      <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-3">
          {(packs ?? []).map((pack) => (
            <Card key={pack.id} className={pack.id === selectedPackId ? "border-primary" : ""}>
              <CardContent className="flex items-center justify-between gap-2 p-3">
                <button
                  type="button"
                  className="w-full text-left text-sm font-medium"
                  onClick={() => setSelectedPackId(pack.id)}
                >
                  {pack.name}
                </button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    deleteMutation.mutate(pack.id);
                  }}
                  disabled={deleteMutation.isPending}
                >
                  {t.common.delete}
                </Button>
              </CardContent>
            </Card>
          ))}
          {(packs ?? []).length === 0 && (
            <Card>
              <CardContent className="p-4 text-sm text-muted-foreground">
                {t.knowledgePacksPage.emptyState}
              </CardContent>
            </Card>
          )}
          {selectedPackId && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle>{selectedPackName}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="rounded-md border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted/50">
                      <tr className="text-left">
                        <th className="px-3 py-2 font-medium">{t.knowledgePacksPage.tableDocument}</th>
                        <th className="px-3 py-2 font-medium">{t.knowledgePacksPage.tableChunks}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(packDocuments ?? []).map((item) => (
                        <tr key={item.document_id} className="border-t">
                          <td className="px-3 py-2">{item.document_title}</td>
                          <td className="px-3 py-2">{item.chunk_count}</td>
                        </tr>
                      ))}
                      {(packDocuments ?? []).length === 0 && (
                        <tr>
                          <td className="px-3 py-3 text-muted-foreground" colSpan={2}>
                            {t.knowledgePacksPage.emptySelectedPack}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                <p className="text-xs text-muted-foreground">{t.knowledgePacksPage.documentsHint}</p>
              </CardContent>
            </Card>
          )}
        </div>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>{t.knowledgePacksPage.createTitle}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input
              id="pack-name"
              value={newKnowledgeName}
              onChange={(event) => setNewKnowledgeName(event.target.value)}
              placeholder={t.knowledgePacksPage.namePlaceholder}
            />
            <Button className="w-full" onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              {t.knowledgePacksPage.createButton}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
