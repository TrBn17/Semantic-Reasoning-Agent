"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAgentSettings } from "@/shared/api/agents";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";

export default function SettingsPage() {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.agents.settings(workspaceId),
    queryFn: () => getAgentSettings(workspaceId),
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 p-6">
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-52 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-6xl p-6 text-sm text-destructive">
        Failed to load workspace settings.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Workspace control plane for provider readiness, model defaults, and routing health.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Provider setup</CardTitle>
            <CardDescription>Credential state and runtime readiness by provider.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {data.providers.map((provider) => (
              <div key={provider.provider} className="rounded-xl border p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{provider.label}</div>
                  <div className={`text-xs ${provider.ready ? "text-emerald-600" : "text-amber-600"}`}>
                    {provider.ready ? "Ready" : "Needs setup"}
                  </div>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{provider.reason}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Readiness</CardTitle>
            <CardDescription>Current workspace model routing posture.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {data.task_assignments.map((assignment) => (
              <div key={assignment.task_type} className="rounded-xl border px-3 py-2">
                <div className="font-medium">{assignment.task_type}</div>
                <div className="text-muted-foreground">
                  {assignment.provider} | {assignment.model}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model catalog</CardTitle>
          <CardDescription>Available runtime models and their current readiness.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {data.models.map((model) => (
            <div key={`${model.provider}:${model.model}`} className="rounded-xl border p-4">
              <div className="font-medium">{model.label}</div>
              <div className="mt-1 text-sm text-muted-foreground">
                {model.provider} | {model.model}
              </div>
              <div className={`mt-2 text-xs ${model.ready ? "text-emerald-600" : "text-amber-600"}`}>
                {model.reason}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
