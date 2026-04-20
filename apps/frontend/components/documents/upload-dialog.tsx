"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
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
import { uploadDocuments } from "@/lib/api/documents";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function UploadDialog() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [tags, setTags] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      if (files.length === 0) throw new Error(t.common.selectAtLeastOneFile);
      return uploadDocuments({
        files,
        workspaceId: workspaceId ?? undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
    },
    onSuccess: ({ uploaded, failed }) => {
      if (uploaded.length > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      }

      if (uploaded.length > 0 && failed.length === 0) {
        toast.success(`${t.common.uploaded} ${uploaded.length} ${t.common.files}`);
        setOpen(false);
      } else if (uploaded.length > 0) {
        toast.warning(
          `${t.common.uploaded} ${uploaded.length} ${t.common.files}, ${t.common.failedToLoadDocuments} ${failed.length}: ${failed
            .slice(0, 2)
            .map((f) => f.filename)
            .join(", ")}`,
        );
      } else {
        toast.error(
          `${t.common.failedToLoadDocuments} ${failed.slice(0, 2).map((f) => f.reason).join(" | ")}`,
        );
      }

      setFiles([]);
      setTags("");
    },
    onError: (err) => toast.error(`${t.common.uploadFailedPrefix} ${(err as Error).message}`),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="h-4 w-4" />
          {t.common.upload}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.common.upload}</DialogTitle>
          <DialogDescription>
            {t.common.uploadDescription}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="file">{t.common.files}</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx,.xlsx"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
            {files.length > 0 && (
              <p className="text-xs text-muted-foreground">
                {t.common.selected} {files.length} {t.common.files}: {files.slice(0, 3).map((f) => f.name).join(", ")}
                {files.length > 3 ? "..." : ""}
              </p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="tags">{t.common.tags} ({t.common.commaSeparated})</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder={t.common.tagsPlaceholder}
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
            {mutation.isPending ? t.common.uploading : t.common.uploadSelected}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
