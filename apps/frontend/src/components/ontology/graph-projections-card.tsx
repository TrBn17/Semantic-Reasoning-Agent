"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { createGraphProjection, deleteGraphProjection, listGraphProjections } from "@/shared/api/ontology";
import { listKnowledgePacks } from "@/shared/api/knowledge-packs";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { notify } from "@/shared/ui/notify";
import { Time } from "@/shared/components/time";

export function GraphProjectionsCard() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);

  const projectionsQuery = useQuery({
    queryKey: queryKeys.ontology.graphProjections(workspaceId),
    queryFn: () => listGraphProjections(workspaceId ?? undefined),
    enabled: !!workspaceId,
  });

  const packsQuery = useQuery({
    queryKey: queryKeys.knowledgePacks.list(workspaceId),
    queryFn: () => listKnowledgePacks(workspaceId),
    enabled: !!workspaceId,
  });

  const packNameById = useMemo(() => {
    const m = new Map<string, string>();
    for (const p of packsQuery.data ?? []) m.set(p.id, p.name);
    return m;
  }, [packsQuery.data]);

  const [open, setOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [packId, setPackId] = useState<string>("");

  const createMutation = useMutation({
    mutationFn: () =>
      createGraphProjection({
        workspace_id: workspaceId as string,
        knowledge_pack_id: packId,
        name: newName.trim(),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.ontology.all });
      setOpen(false);
      setNewName("");
      setPackId("");
      notify.success(t.graphProjections.created);
    },
    onError: (err) => {
      notify.error(err, t.graphProjections.createFailedPrefix);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteGraphProjection(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.ontology.all });
      notify.success(t.graphProjections.deleted);
    },
    onError: (err) => {
      notify.error(err, t.graphProjections.deleteFailedPrefix);
    },
  });

  const canSubmit =
    !!workspaceId &&
    packId.length > 0 &&
    newName.trim().length > 0 &&
    !createMutation.isPending;

  if (!workspaceId) return null;

  return (
    <Card className="rounded-2xl border">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="text-base">{t.graphProjections.title}</CardTitle>
            <CardDescription className="mt-1">{t.graphProjections.description}</CardDescription>
          </div>
          <Dialog
            open={open}
            onOpenChange={(next) => {
              setOpen(next);
              if (!next) {
                setNewName("");
                setPackId("");
              }
            }}
          >
            <DialogTrigger asChild>
              <Button type="button" size="sm" variant="outline" className="shrink-0">
                <Plus className="mr-1 h-4 w-4" />
                {t.graphProjections.create}
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>{t.graphProjections.dialogTitle}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="gp-name">{t.graphProjections.nameLabel}</Label>
                  <Input
                    id="gp-name"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder={t.graphProjections.namePlaceholder}
                  />
                </div>
                <div className="space-y-2">
                  <Label>{t.graphProjections.packLabel}</Label>
                  {packsQuery.isLoading ? (
                    <Skeleton className="h-9 w-full" />
                  ) : (packsQuery.data ?? []).length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t.graphProjections.noKnowledgePacks}</p>
                  ) : (
                    <Select value={packId || undefined} onValueChange={setPackId}>
                      <SelectTrigger>
                        <SelectValue placeholder={t.graphProjections.packPlaceholder} />
                      </SelectTrigger>
                      <SelectContent>
                        {(packsQuery.data ?? []).map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                  {t.common.cancel}
                </Button>
                <Button
                  type="button"
                  disabled={!canSubmit}
                  onClick={() => createMutation.mutate()}
                >
                  {t.common.create}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {projectionsQuery.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : projectionsQuery.isError ? (
          <p className="text-sm text-destructive">{t.graphProjections.loadFailed}</p>
        ) : (projectionsQuery.data ?? []).length === 0 ? (
          <p className="text-sm text-muted-foreground">{t.graphProjections.empty}</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t.graphProjections.columnName}</TableHead>
                <TableHead>{t.graphProjections.columnPack}</TableHead>
                <TableHead className="font-mono text-xs">{t.graphProjections.columnGroupId}</TableHead>
                <TableHead>{t.graphProjections.columnCreated}</TableHead>
                <TableHead className="w-[52px]" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(projectionsQuery.data ?? []).map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.name}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {packNameById.get(row.knowledge_pack_id) ?? row.knowledge_pack_id.slice(0, 8)}
                  </TableCell>
                  <TableCell className="max-w-[220px] truncate font-mono text-[11px]" title={row.graphiti_group_id}>
                    {row.graphiti_group_id}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                    <Time value={row.created_at} className="inline" />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      aria-label={t.graphProjections.deleteAria}
                      disabled={deleteMutation.isPending}
                      onClick={() => {
                        const ok = window.confirm(
                          t.graphProjections.deleteConfirm.replace("{name}", row.name),
                        );
                        if (ok) deleteMutation.mutate(row.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
