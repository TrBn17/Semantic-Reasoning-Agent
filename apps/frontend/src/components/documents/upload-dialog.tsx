"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
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
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { useI18n } from "@/shared/i18n/use-language";

export function UploadDialog() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [tags, setTags] = useState("");
  const [ingestionMode, setIngestionMode] = useState<"ontology" | "retrieval" | "both">("both");
  const { data: capabilities } = useQuery({
    queryKey: ["documents", "options"],
    queryFn: getDocumentIngestionCapabilities,
  });

  const mutation = useMutation({
    mutationFn: () => {
      if (files.length === 0) throw new Error(t.documents.toasts.selectFile);
      return uploadDocuments({
        files,
        workspaceId: workspaceId ?? undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        ingestionMode,
      });
    },
    onSuccess: ({ uploaded, failed }) => {
      if (uploaded.length > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      }

      if (uploaded.length > 0 && failed.length === 0) {
        toast.success(t.documents.toasts.uploadSuccess.replace("{count}", uploaded.length.toString()));
        setOpen(false);
      } else if (uploaded.length > 0) {
        toast.warning(
          t.documents.toasts.uploadPartial
            .replace("{uploaded}", uploaded.length.toString())
            .replace("{failed}", failed.length.toString())
            .replace("{filenames}", failed.slice(0, 2).map((f) => f.filename).join(", "))
        );
      } else {
        toast.error(
          t.documents.toasts.uploadFailed.replace("{reason}", failed.slice(0, 2).map((f) => f.reason).join(" | "))
        );
      }

      setFiles([]);
      setTags("");
      setIngestionMode("both");
    },
    onError: (err) => toast.error(t.documents.toasts.uploadFailed.replace("{reason}", (err as Error).message)),
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
          <DialogDescription>
            {t.documents.uploadDescription}
          </DialogDescription>
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
            <p className="text-xs text-muted-foreground">
              {(capabilities?.ingestion_mode_options ?? []).find(
                (option) => option.value === ingestionMode,
              )?.description ?? t.documents.ingestionModeHint}
            </p>
          </div>
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
