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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { uploadDocuments } from "@/lib/api/documents";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export function UploadDialog() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [tags, setTags] = useState("");
  const [pdfMode, setPdfMode] = useState<"fast" | "accurate">("fast");
  const hasPdf = files.some((file) => file.name.toLowerCase().endsWith(".pdf"));

  const mutation = useMutation({
    mutationFn: () => {
      if (files.length === 0) throw new Error("Select at least one file to upload");
      return uploadDocuments({
        files,
        workspaceId: workspaceId ?? undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        pdfMode,
      });
    },
    onSuccess: ({ uploaded, failed }) => {
      if (uploaded.length > 0) {
        queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      }

      if (uploaded.length > 0 && failed.length === 0) {
        toast.success(`Uploaded ${uploaded.length} file(s)`);
        setOpen(false);
      } else if (uploaded.length > 0) {
        toast.warning(
          `Uploaded ${uploaded.length} file(s), failed ${failed.length}: ${failed
            .slice(0, 2)
            .map((f) => f.filename)
            .join(", ")}`,
        );
      } else {
        toast.error(
          `Upload failed: ${failed.slice(0, 2).map((f) => f.reason).join(" | ")}`,
        );
      }

      setFiles([]);
      setTags("");
      setPdfMode("fast");
    },
    onError: (err) => toast.error(`Upload failed: ${(err as Error).message}`),
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload className="h-4 w-4" />
          Upload
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Upload a document</DialogTitle>
          <DialogDescription>
            PDF, DOCX, XLSX, or CSV. Parsed and indexed by the ingestion worker.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="file">File</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx,.xlsx,.csv"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            />
            {files.length > 0 && (
              <p className="text-xs text-muted-foreground">
                Selected {files.length} file(s): {files.slice(0, 3).map((f) => f.name).join(", ")}
                {files.length > 3 ? "..." : ""}
              </p>
            )}
          </div>
          {hasPdf && (
            <div className="space-y-1">
              <Label htmlFor="pdf-mode">PDF mode</Label>
              <Select value={pdfMode} onValueChange={(value) => setPdfMode(value as "fast" | "accurate")}>
                <SelectTrigger id="pdf-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fast">Fast</SelectItem>
                  <SelectItem value="accurate">Accurate</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
          <div className="space-y-1">
            <Label htmlFor="tags">Tags (comma separated)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. policy,2025"
            />
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              Cancel
            </Button>
          </DialogClose>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || files.length === 0}
          >
            {mutation.isPending ? "Uploading..." : "Upload selected"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
