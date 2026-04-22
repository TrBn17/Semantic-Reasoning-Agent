"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchMe } from "@/shared/api/auth";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";

export function useActiveWorkspaceId() {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const { data } = useQuery({
    queryKey: queryKeys.me,
    queryFn: fetchMe,
  });

  return workspaceId ?? data?.active_workspace.id ?? null;
}
