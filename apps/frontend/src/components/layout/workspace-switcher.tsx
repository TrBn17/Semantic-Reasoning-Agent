"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronDown, Plus, Check, Loader2, Pencil, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createWorkspace,
  deleteWorkspace,
  fetchMe,
  fetchWorkspaces,
  updateWorkspace,
} from "@/shared/api/auth";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { useI18n } from "@/shared/i18n/use-language";
import { notify } from "@/shared/ui/notify";

export function WorkspaceSwitcher() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const { workspaceId, setWorkspaceId } = useWorkspaceStore();
  
  const { data: user } = useQuery({
    queryKey: queryKeys.me,
    queryFn: fetchMe,
  });

  const { data: workspaces, isLoading } = useQuery({
    queryKey: ["workspaces"],
    queryFn: fetchWorkspaces,
  });

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [editingWorkspaceId, setEditingWorkspaceId] = useState<string>("");
  const [editingWorkspaceName, setEditingWorkspaceName] = useState("");

  const activeWorkspace =
    workspaces?.find((ws) => ws.id === workspaceId) ||
    (user?.active_workspace?.id === workspaceId ? user.active_workspace : null) || {
      id: workspaceId || "unknown",
      name: workspaceId || "Unknown",
    };

  const createMutation = useMutation({
    mutationFn: async () => {
      const workspaceNameInput = newWorkspaceName.trim();
      if (!workspaceNameInput) {
        throw new Error(t.workspaceSwitcher.toasts.nameRequired);
      }
      return createWorkspace({
        name: workspaceNameInput,
      });
    },
    onSuccess: (workspace) => {
      setWorkspaceId(workspace.id);
      setIsCreateDialogOpen(false);
      setNewWorkspaceName("");
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      notify.success(`${t.workspaceSwitcher.toasts.switchedTo} ${workspace.name}`);
    },
    onError: (error) => {
      notify.error(error, t.common.error);
    },
  });

  const renameMutation = useMutation({
    mutationFn: async () => {
      const name = editingWorkspaceName.trim();
      if (!editingWorkspaceId) {
        throw new Error(t.workspaceSwitcher.toasts.selectWorkspace);
      }
      if (!name) {
        throw new Error(t.workspaceSwitcher.toasts.nameRequired);
      }
      return updateWorkspace(editingWorkspaceId, { name });
    },
    onSuccess: (workspace) => {
      setIsEditDialogOpen(false);
      setEditingWorkspaceId("");
      setEditingWorkspaceName("");
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      notify.success(t.workspaceSwitcher.toasts.workspaceUpdated.replace("{name}", workspace.name));
    },
    onError: (error) => {
      notify.error(error, t.common.error);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (workspaceToDelete: { id: string; name: string }) => {
      await deleteWorkspace(workspaceToDelete.id);
      return workspaceToDelete;
    },
    onSuccess: (workspace) => {
      const fallbackWorkspaceId = user?.active_workspace?.id ?? null;
      if (workspace.id === workspaceId) {
        setWorkspaceId(fallbackWorkspaceId);
      }
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      notify.success(t.workspaceSwitcher.toasts.workspaceDeleted.replace("{name}", workspace.name));
    },
    onError: (error) => {
      notify.error(error, t.common.error);
    },
  });

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="flex items-center gap-2 px-2 h-9 border border-transparent hover:border-border transition-colors">
            <Badge variant="secondary" className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider">
              {activeWorkspace.name}
            </Badge>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-64">
          <DropdownMenuLabel className="text-xs font-normal text-muted-foreground uppercase tracking-widest">
            {t.workspaceSwitcher.switchWorkspace}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          <div className="max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : (
              workspaces?.map((ws) => {
                const isDefault = ws.id === user?.active_workspace?.id;
                return (
                  <DropdownMenuItem
                    key={ws.id}
                    onClick={() => {
                      setWorkspaceId(ws.id);
                      notify.success(`${t.workspaceSwitcher.toasts.switchedTo} ${ws.name}`);
                    }}
                    className="flex items-center justify-between gap-2"
                  >
                    <span className={ws.id === workspaceId ? "font-bold" : ""}>{ws.name}</span>
                    <div className="flex items-center gap-1">
                      {ws.id === workspaceId && <Check className="h-4 w-4 text-primary" />}
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-6 w-6"
                        onClick={(event) => {
                          event.preventDefault();
                          event.stopPropagation();
                          setEditingWorkspaceId(ws.id);
                          setEditingWorkspaceName(ws.name);
                          setIsEditDialogOpen(true);
                        }}
                        aria-label={t.workspaceSwitcher.renameWorkspace}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      {!isDefault && (
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-6 w-6 text-destructive hover:text-destructive"
                          onClick={(event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            const confirmed = window.confirm(
                              t.workspaceSwitcher.deleteConfirm.replace("{name}", ws.name),
                            );
                            if (!confirmed) return;
                            deleteMutation.mutate({ id: ws.id, name: ws.name });
                          }}
                          aria-label={t.workspaceSwitcher.deleteWorkspace}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  </DropdownMenuItem>
                );
              })
            )}
          </div>

          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsCreateDialogOpen(true)} className="text-primary focus:text-primary">
            <Plus className="mr-2 h-4 w-4" />
            {t.workspaceSwitcher.createWorkspace}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="sm:max-w-md" closeLabel={t.common.accessibility.closeDialog}>
          <DialogHeader>
            <DialogTitle>{t.workspaceSwitcher.createTitle}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">{t.workspaceSwitcher.workspaceNameLabel}</Label>
              <Input
                id="name"
                placeholder={t.workspaceSwitcher.workspaceNamePlaceholder}
                value={newWorkspaceName}
                onChange={(e) => setNewWorkspaceName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              {t.workspaceSwitcher.createAndSwitch}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-md" closeLabel={t.common.accessibility.closeDialog}>
          <DialogHeader>
            <DialogTitle>{t.workspaceSwitcher.renameTitle}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">{t.workspaceSwitcher.workspaceNameLabel}</Label>
              <Input
                id="edit-name"
                placeholder={t.workspaceSwitcher.workspaceNamePlaceholder}
                value={editingWorkspaceName}
                onChange={(e) => setEditingWorkspaceName(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button onClick={() => renameMutation.mutate()} disabled={renameMutation.isPending}>
              {t.common.save}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
