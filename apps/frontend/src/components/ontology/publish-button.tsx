"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Rocket } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { publishBuild } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import type { OntologyBuildResponse } from "@/shared/api/types";

export function PublishButton({ build }: { build: OntologyBuildResponse }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => publishBuild(build.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all });
      toast.success("Ontology published");
    },
    onError: (err) => toast.error(`Publish failed: ${(err as Error).message}`),
  });

  const canPublish =
    (build.status === "completed" || build.status === "published") &&
    build.pending_entity_count === 0 &&
    build.pending_relation_count === 0;

  return (
    <div className="flex items-center gap-2">
      <Button
        onClick={() => mutation.mutate()}
        disabled={!canPublish || mutation.isPending}
      >
        <Rocket className="h-4 w-4" />
        {build.status === "published" ? "Re-publish" : "Publish"}
      </Button>
      {!canPublish && (
        <span className="text-xs text-muted-foreground">
          {build.status !== "completed" && build.status !== "published"
            ? `Waiting for build (${build.status})`
            : "Resolve pending candidates first"}
        </span>
      )}
    </div>
  );
}
