"use client";

import { useQuery, type UseQueryOptions, type UseQueryResult } from "@tanstack/react-query";
import { listSettingsModels } from "@/shared/api/settings";
import type { SettingsModelOption } from "@/shared/api/types";
import { queryKeys } from "@/shared/query/keys";
import { useActiveWorkspaceId } from "./use-active-workspace-id";

/**
 * Central definition for the settings model catalog: same queryKey + queryFn
 * as GET /api/v1/settings/models (with workspace_id when resolved).
 */
export function settingsModelsQueryOptions(workspaceId: string | null) {
  return {
    queryKey: queryKeys.settings.models(workspaceId),
    queryFn: () => listSettingsModels(workspaceId),
  } as const;
}

export function useSettingsModelsQuery(
  options?: Omit<
    UseQueryOptions<SettingsModelOption[], Error, SettingsModelOption[]>,
    "queryKey" | "queryFn"
  >,
): UseQueryResult<SettingsModelOption[], Error> {
  const workspaceId = useActiveWorkspaceId();
  return useQuery<SettingsModelOption[], Error, SettingsModelOption[]>({
    ...settingsModelsQueryOptions(workspaceId),
    ...options,
  });
}
