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
import { uploadDocument } from "@/lib/api/documents";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export function UploadDialog() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error("Select a file to upload");
      return uploadDocument({
        file,
        title: title || undefined,
        workspaceId: workspaceId ?? undefined,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      });
    },
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      toast.success(`Uploaded ${doc.filename}`);
      setFile(null);
      setTitle("");
      setTags("");
      setOpen(false);
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
            PDF, DOCX, or XLSX. Parsed and indexed by the ingestion worker.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="file">File</Label>
            <Input
              id="file"
              type="file"
              accept=".pdf,.docx,.xlsx"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="title">Title (optional)</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Defaults to filename"
            />
          </div>
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
            disabled={mutation.isPending || !file}
          >
            {mutation.isPending ? "Uploading..." : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
