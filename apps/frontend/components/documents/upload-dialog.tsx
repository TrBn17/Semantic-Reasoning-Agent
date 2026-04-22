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
import { getDocumentIngestionCapabilities, uploadDocuments } from "@/lib/api/documents";
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
  const [pdfMode, setPdfMode] = useState<"fast" | "accurate">("fast");
  const [outputFormat, setOutputFormat] = useState<"markdown" | "html" | "json" | "chunks">("markdown");
  const [extractImages, setExtractImages] = useState(true);
  const hasPdf = files.some((file) => file.name.toLowerCase().endsWith(".pdf"));
  const hasMarkerFile = files.some((file) => file.name.toLowerCase().split(".").pop() !== "csv");
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
        pdfMode,
        outputFormat,
        extractImages,
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
      setPdfMode("fast");
      setOutputFormat("markdown");
      setExtractImages(true);
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
      <DialogContent>
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
              accept=".pdf,.docx,.xlsx,.csv"
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
          {hasPdf && (
            <div className="space-y-1">
              <Label htmlFor="pdf-mode">{t.documents.pdfModeLabel}</Label>
              <Select value={pdfMode} onValueChange={(value) => setPdfMode(value as "fast" | "accurate")}>
                <SelectTrigger id="pdf-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(capabilities?.pdf_mode_options ?? [
                    { value: "fast", label: t.documents.pdfModeFast },
                    { value: "accurate", label: t.documents.pdfModeAccurate },
                  ]).map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {hasMarkerFile && (
            <div className="space-y-4 rounded-md border p-3">
              <div className="space-y-1">
                <Label htmlFor="output-format">{t.documents.outputFormatLabel}</Label>
                <Select
                  value={outputFormat}
                  onValueChange={(value) => setOutputFormat(value as "markdown" | "html" | "json" | "chunks")}
                >
                  <SelectTrigger id="output-format">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(capabilities?.output_format_options ?? [
                      { value: "markdown", label: t.documents.outputFormatMarkdown },
                      { value: "html", label: t.documents.outputFormatHtml },
                      { value: "json", label: t.documents.outputFormatJson },
                      { value: "chunks", label: t.documents.outputFormatChunks },
                    ]).map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {
                    (capabilities?.output_format_options ?? []).find((option) => option.value === outputFormat)
                      ?.description ?? t.documents.outputFormatHint
                  }
                </p>
              </div>
              {capabilities?.supports_extract_images !== false && (
                <label className="flex items-start gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 rounded border"
                    checked={extractImages}
                    onChange={(e) => setExtractImages(e.target.checked)}
                  />
                  <span>
                    <span className="font-medium">{t.documents.extractImagesLabel}</span>
                    <span className="block text-xs text-muted-foreground">
                      {t.documents.extractImagesHint}
                    </span>
                  </span>
                </label>
              )}
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
