"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
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
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { listDocuments } from "@/lib/api/documents";
import { createBuild } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";

export function NewBuildDialog() {
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const [open, setOpen] = useState(false);
  const [documentId, setDocumentId] = useState<string | undefined>();

  const { data: documents } = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: listDocuments,
  });

  const mutation = useMutation({
    mutationFn: () => {
      if (!documentId) throw new Error("Pick a document");
      return createBuild({
        document_id: documentId,
        workspace_id: workspaceId ?? undefined,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      toast.success("Build queued");
      setOpen(false);
      setDocumentId(undefined);
    },
    onError: (err) => toast.error(`Build failed: ${(err as Error).message}`),
  });

  const indexed = (documents ?? []).filter((d) => d.status === "indexed");

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4" />
          New build
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Run ontology extraction</DialogTitle>
          <DialogDescription>
            Pick an indexed document. The worker extracts candidate entities
            and relations, then they land in the review queue.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label>Document</Label>
          <Select value={documentId} onValueChange={setDocumentId}>
            <SelectTrigger>
              <SelectValue placeholder="Select an indexed document" />
            </SelectTrigger>
            <SelectContent>
              {indexed.map((d) => (
                <SelectItem key={d.id} value={d.id}>
                  {d.title}
                </SelectItem>
              ))}
              {indexed.length === 0 && (
                <div className="p-2 text-xs text-muted-foreground">
                  No indexed documents. Upload and wait for indexing to finish.
                </div>
              )}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              Cancel
            </Button>
          </DialogClose>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!documentId || mutation.isPending}
          >
            {mutation.isPending ? "Queueing..." : "Start build"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
