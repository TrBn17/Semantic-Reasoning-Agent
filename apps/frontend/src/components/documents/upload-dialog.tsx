"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getDocumentIngestionCapabilities, uploadDocuments } from "@/shared/api/documents";
import { listKnowledgePacks } from "@/shared/api/knowledge-packs";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { useI18n } from "@/shared/i18n/use-language";
import { notify } from "@/shared/ui/notify";

export function UploadDialog() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [tags, setTags] = useState("");
  const [ingestionMode, setIngestionMode] = useState<"ontology" | "retrieval" | "both">("both");
  const [knowledgePackId, setKnowledgePackId] = useState<string>("");
  const requiresKnowledgePack = ingestionMode === "retrieval" || ingestionMode === "both";
  const { data: capabilities } = useQuery({
    queryKey: ["documents", "options"],
    queryFn: getDocumentIngestionCapabilities,
  });
  const { data: knowledgePacks } = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
    enabled: open && Boolean(workspaceId),
  });

  const mutation = useMutation({
    mutationFn: async () => {
      if (files.length === 0) throw new Error(t.documents.toasts.selectFile);
      if (!workspaceId) throw new Error(t.documents.toasts.workspaceRequired);
      let resolvedKnowledgePackId: string | undefined;
      if (requiresKnowledgePack) {
        if (knowledgePackId) {
          resolvedKnowledgePackId = knowledgePackId;
        } else {
          throw new Error(t.documents.toasts.knowledgePackRequired);
        }
      }
      return uploadDocuments({
        files,
        workspaceId: workspaceId ?? undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        ingestionMode,
        knowledgePackId: resolvedKnowledgePackId,
      });
    },
    onSuccess: ({ uploaded, failed }) => {
      if (uploaded.length > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      }

      if (uploaded.length > 0 && failed.length === 0) {
        notify.success(t.documents.toasts.uploadSuccess.replace("{count}", uploaded.length.toString()));
        setOpen(false);
      } else if (uploaded.length > 0) {
        notify.warning(
          t.documents.toasts.uploadPartial
            .replace("{uploaded}", uploaded.length.toString())
            .replace("{failed}", failed.length.toString())
            .replace("{filenames}", failed.slice(0, 2).map((f) => f.filename).join(", "))
        );
      } else {
        notify.error(
          t.documents.toasts.uploadFailed.replace("{reason}", failed.slice(0, 2).map((f) => f.reason).join(" | ")),
          t.documents.toasts.uploadFailed.replace("{reason}", t.common.error),
        );
      }

      setFiles([]);
      setTags("");
      setIngestionMode("both");
      setKnowledgePackId("");
    },
    onError: (err) => {
      const message = (err as Error).message;
      const normalized = message.toLowerCase();
      const reason = normalized.includes("out-of-scope document ids")
        ? t.documents.toasts.outOfScopeDocument
        : message;
      notify.error(
        t.documents.toasts.uploadFailed.replace("{reason}", reason),
        t.documents.toasts.uploadFailed.replace("{reason}", t.common.error),
      );
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="h-4 w-4" />
          {t.common.upload}
        </Button>
      </DialogTrigger>
      <DialogContent closeLabel={t.common.accessibility.closeDialog}>
        <DialogHeader>
          <DialogTitle>{t.documents.uploadTitle}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="file">{t.documents.fileLabel}</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx,.xlsx,.csv,.pptx,.md,.markdown,.txt,.html,.htm,.json,.xml,.epub,.zip,.jpg,.jpeg,.png,.gif,.webp,.bmp,.tif,.tiff"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
            {files.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {t.documents.selectedFiles.replace("{count}", files.length.toString())}: {files.slice(0, 3).map((f) => f.name).join(", ")}
                {files.length > 3 ? "..." : ""}
              </p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="ingestion-mode">{t.documents.ingestionModeLabel}</Label>
            <Select
              value={ingestionMode}
              onValueChange={(value) =>
                setIngestionMode(value as "ontology" | "retrieval" | "both")
              }
            >
              <SelectTrigger id="ingestion-mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(capabilities?.ingestion_mode_options ?? [
                  { value: "ontology", label: t.documents.ingestionModeOntology },
                  { value: "retrieval", label: t.documents.ingestionModeRetrieval },
                  { value: "both", label: t.documents.ingestionModeBoth },
                ]).map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {requiresKnowledgePack && (
            <div className="space-y-1">
              <Label htmlFor="knowledge-pack">{t.documents.knowledgePack.label}</Label>
              <Select value={knowledgePackId} onValueChange={setKnowledgePackId}>
                <SelectTrigger id="knowledge-pack">
                  <SelectValue placeholder={t.documents.knowledgePack.selectPlaceholder} />
                </SelectTrigger>
                <SelectContent>
                  {(knowledgePacks ?? []).map((pack) => (
                    <SelectItem key={pack.id} value={pack.id}>
                      {pack.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-1">
            <Label htmlFor="tags">{t.documents.tagsLabel}</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder={t.documents.tagsPlaceholder}
            />
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              {t.common.cancel}
            </Button>
          </DialogClose>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || files.length === 0}
          >
            {mutation.isPending ? t.documents.uploading : t.documents.uploadSelected}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
