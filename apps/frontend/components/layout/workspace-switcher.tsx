"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ChevronDown, Plus, Check, Loader2 } from "lucide-react";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchMe, fetchWorkspaces } from "@/lib/api/auth";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { toast } from "sonner";
import { useI18n } from "@/src/shared/i18n/use-language";

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

  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newWorkspaceId, setNewWorkspaceId] = useState("");
  const [newWorkspaceName, setNewWorkspaceName] = useState("");

  const activeWorkspace = workspaces?.find(ws => ws.id === workspaceId) || 
                          (user?.active_workspace?.id === workspaceId ? user.active_workspace : null) ||
                          { id: workspaceId || "unknown", name: workspaceId || "Unknown" };

  const handleCreateWorkspace = () => {
    if (!newWorkspaceId.trim()) {
      toast.error(t.workspaceSwitcher.toasts.idRequired);
      return;
    }
    
    // Trong kiến trúc hiện tại, chúng ta chỉ cần set ID mới vào store.
    // Khi frontend gọi các API với ID này, backend sẽ tự động "hiểu" là workspace mới.
    const slugifiedId = newWorkspaceId.toLowerCase().replace(/[^a-z0-9-]/g, "-");
    setWorkspaceId(slugifiedId);
    
    // Refresh danh sách để hiện cái mới (backend sẽ tổng hợp từ DB)
    setTimeout(() => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    }, 1000);
    
    setIsDialogOpen(false);
    setNewWorkspaceId("");
    setNewWorkspaceName("");
    toast.success(`${t.workspaceSwitcher.toasts.switchedTo} ${slugifiedId}`);
  };

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
              workspaces?.map((ws) => (
                <DropdownMenuItem
                  key={ws.id}
                  onClick={() => {
                    setWorkspaceId(ws.id);
                    toast.success(`${t.workspaceSwitcher.toasts.switchedTo} ${ws.name}`);
                  }}
                  className="flex items-center justify-between"
                >
                  <span className={ws.id === workspaceId ? "font-bold" : ""}>
                    {ws.name}
                  </span>
                  {ws.id === workspaceId && <Check className="h-4 w-4 text-primary" />}
                </DropdownMenuItem>
              ))
            )}
          </div>

          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsDialogOpen(true)} className="text-primary focus:text-primary">
            <Plus className="mr-2 h-4 w-4" />
            {t.workspaceSwitcher.createWorkspace}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t.workspaceSwitcher.createTitle}</DialogTitle>
            <DialogDescription>
              {t.workspaceSwitcher.createDescription}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="id">{t.workspaceSwitcher.workspaceIdLabel}</Label>
              <Input
                id="id"
                placeholder={t.workspaceSwitcher.workspaceIdPlaceholder}
                value={newWorkspaceId}
                onChange={(e) => setNewWorkspaceId(e.target.value)}
              />
              <p className="text-[10px] text-muted-foreground italic">
                {t.workspaceSwitcher.workspaceIdHint}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>{t.common.cancel}</Button>
            <Button onClick={handleCreateWorkspace}>{t.workspaceSwitcher.createAndSwitch}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
