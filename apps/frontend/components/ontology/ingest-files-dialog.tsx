"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload } from "lucide-react";
import { useRef, useState } from "react";
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
import { ingestFilesAndPublish } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function IngestFilesDialog() {
  const { t } = useI18n();
  const ig = t.knowledgeGraph.ingestDialog;
  const queryClient = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);

  const mutation = useMutation({
    mutationFn: (files: File[]) => ingestFilesAndPublish(files, workspaceId ?? undefined),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      const builds = res.build_ids.map((id) => id.slice(0, 8)).join(", ");
      toast.success(
        ig.toastSuccess.replace("{n}", String(res.document_ids.length)).replace("{builds}", builds),
      );
      setOpen(false);
    },
    onError: (err) => toast.error(`${ig.toastError} ${(err as Error).message}`),
  });

  const onPick: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (files.length === 0) return;
    mutation.mutate(files);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="h-4 w-4" />
          {ig.trigger}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{ig.title}</DialogTitle>
          <DialogDescription>{ig.description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            accept=".pdf,.doc,.docx,.xlsx,.xls"
            onChange={onPick}
          />
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            disabled={mutation.isPending}
            onClick={() => inputRef.current?.click()}
          >
            {mutation.isPending ? ig.uploading : ig.chooseFiles}
          </Button>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" type="button">
              {ig.close}
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
