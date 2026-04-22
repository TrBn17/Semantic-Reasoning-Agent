"use client";

import { useQuery } from "@tanstack/react-query";
import { CircleUserRound } from "lucide-react";
import { fetchMe } from "@/shared/api/auth";
import { queryKeys } from "@/shared/query/keys";
import { Badge } from "@/components/ui/badge";

export function UserMenu() {
  const { data } = useQuery({
    queryKey: queryKeys.me,
    queryFn: fetchMe,
  });

  return (
    <div className="hidden items-center gap-2 rounded-md border px-2 py-1 text-xs text-muted-foreground lg:inline-flex">
      <CircleUserRound className="h-3.5 w-3.5" />
      <span>{data?.display_name ?? "User"}</span>
      {data?.active_workspace?.name ? <Badge variant="outline">{data.active_workspace.name}</Badge> : null}
    </div>
  );
}
