"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { DocumentTable } from "@/components/documents/document-table";
import { UploadDialog } from "@/components/documents/upload-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { listDocuments } from "@/shared/api/documents";
import { addKnowledgePackDocument, listKnowledgePacks } from "@/shared/api/knowledge-packs";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { notify } from "@/shared/ui/notify";

export default function DocumentsPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [knowledgeId, setKnowledgeId] = useState<string>("");
  const [documentId, setDocumentId] = useState<string>("");

  const { data: documents } = useQuery({
    queryKey: ["documents", "list", workspaceId ?? null],
    queryFn: () => listDocuments(workspaceId),
  });

  const { data: knowledgeCollections } = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
    enabled: Boolean(workspaceId),
  });

  const addDocumentMutation = useMutation({
    mutationFn: async () => {
      if (!knowledgeId || !documentId) {
        throw new Error(t.documents.toasts.knowledgePackRequired);
      }
      return addKnowledgePackDocument(knowledgeId, { document_id: documentId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.knowledgePacks.all });
      setDocumentId("");
      notify.success(t.documents.toasts.documentAddedToKnowledge);
    },
    onError: (error) => {
      notify.error(error, t.common.error);
    },
  });

  const workspaceDocuments = documents ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{t.pages.documents.title}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline">
            <Link href="/knowledge">{t.nav.knowledgePacks}</Link>
          </Button>
          <UploadDialog />
        </div>
      </div>
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] md:items-end">
          <div className="space-y-1">
            <Label htmlFor="knowledge-select">{t.documents.knowledgePack.label}</Label>
            <Select value={knowledgeId} onValueChange={setKnowledgeId}>
              <SelectTrigger id="knowledge-select">
                <SelectValue placeholder={t.documents.knowledgePack.selectPlaceholder} />
              </SelectTrigger>
              <SelectContent>
                {(knowledgeCollections ?? []).map((item) => (
                  <SelectItem key={item.id} value={item.id}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label htmlFor="document-select">{t.documents.knowledgePack.documentSelectLabel}</Label>
            <Select value={documentId} onValueChange={setDocumentId}>
              <SelectTrigger id="document-select">
                <SelectValue placeholder={t.documents.knowledgePack.documentSelectPlaceholder} />
              </SelectTrigger>
              <SelectContent>
                {workspaceDocuments.map((doc) => (
                  <SelectItem key={doc.id} value={doc.id}>
                    {doc.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={() => addDocumentMutation.mutate()}
            disabled={addDocumentMutation.isPending || !knowledgeId || !documentId}
          >
            {t.documents.knowledgePack.addButton}
          </Button>
        </CardContent>
      </Card>
      <DocumentTable />
    </div>
  );
}
