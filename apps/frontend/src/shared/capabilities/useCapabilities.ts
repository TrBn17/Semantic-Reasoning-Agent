"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSettings } from "@/shared/api/settings";
import { listWorkflows } from "@/shared/api/workflows";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { BASE_CAPABILITIES, mergeCapabilities, type Capabilities } from "./capabilities";

export function useCapabilities(): Capabilities {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const settingsQuery = useQuery({
    queryKey: ["settings", "capabilities", workspaceId ?? null],
    queryFn: () => getSettings(workspaceId),
  });
  const workflowsQuery = useQuery({
    queryKey: ["workflows", "capabilities"],
    queryFn: listWorkflows,
    retry: 0,
  });

  return useMemo(
    () =>
      mergeCapabilities(BASE_CAPABILITIES, {
        workflowsAvailable: workflowsQuery.isSuccess,
        tasksAvailable: BASE_CAPABILITIES.tasksAvailable,
        settingsAvailable: settingsQuery.isSuccess || BASE_CAPABILITIES.settingsAvailable,
      }),
    [settingsQuery.isSuccess, workflowsQuery.isSuccess],
  );
}
