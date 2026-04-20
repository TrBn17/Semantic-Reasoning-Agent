"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchMe } from "@/lib/api/auth";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { useI18n } from "@/src/shared/i18n/use-language";

export function WorkspaceBadge() {
  const { t } = useI18n();
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.me,
    queryFn: fetchMe,
  });
  const setWorkspaceId = useWorkspaceStore((s) => s.setWorkspaceId);

  useEffect(() => {
    if (data?.active_workspace?.id) {
      setWorkspaceId(data.active_workspace.id);
    }
  }, [data?.active_workspace?.id, setWorkspaceId]);

  if (isLoading) return <Skeleton className="h-8 w-40" />;
  if (isError || !data)
    return (
      <Badge variant="destructive" className="text-xs">
        {t.common.serviceUnavailable}
      </Badge>
    );

  return (
    <div className="flex items-center gap-2 text-sm">
      <Badge variant="secondary">{data.active_workspace.name}</Badge>
      <span className="hidden text-muted-foreground md:inline">
        {data.display_name}
      </span>
    </div>
  );
}
