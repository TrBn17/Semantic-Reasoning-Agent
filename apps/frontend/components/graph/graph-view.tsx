"use client";

import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useCallback, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getGraph } from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import {
  entityToNode,
  relationToEdge,
} from "@/src/shared/api/adapters/ontology";
import { track } from "@/src/shared/telemetry/track";
import type {
  GraphEdgeViewModel,
  GraphNodeViewModel,
} from "@/src/entities/ontology/types";
import { formatDateTime } from "@/lib/utils";

const GraphCanvas = dynamic(
  () =>
    import("@/components/graph/graph-canvas").then((m) => ({
      default: m.GraphCanvas,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="h-full min-h-[400px] w-full p-6">
        <Skeleton className="h-full w-full" />
      </div>
    ),
  },
);

type Selection =
  | { kind: "node"; node: GraphNodeViewModel }
  | { kind: "edge"; edge: GraphEdgeViewModel; source: GraphNodeViewModel; target: GraphNodeViewModel }
  | null;

export function GraphView() {
  const workspaceId = useWorkspaceStore((s) => s.workspaceId);
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });
  const [selection, setSelection] = useState<Selection>(null);

  const nodes = useMemo(() => (data?.entities ?? []).map(entityToNode), [data?.entities]);
  const edges = useMemo(() => (data?.relations ?? []).map(relationToEdge), [data?.relations]);
  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  const handleSelect = useCallback(
    (sel: { kind: "node"; node: GraphNodeViewModel } | { kind: "edge"; edge: GraphEdgeViewModel } | null) => {
      if (!sel) {
        setSelection(null);
        return;
      }
      if (sel.kind === "node") {
        setSelection({ kind: "node", node: sel.node });
        track("graph_node_opened", { entity_id: sel.node.id });
        return;
      }

      const source = nodeMap.get(sel.edge.sourceId);
      const target = nodeMap.get(sel.edge.targetId);
      if (source && target) {
        setSelection({
          kind: "edge",
          edge: sel.edge,
          source,
          target,
        });
      }
    },
    [nodeMap],
  );

  return (
    <div className="flex h-full w-full flex-col">
      <header className="flex items-start justify-between border-b bg-muted/20 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Graph</h1>
          <p className="text-xs text-muted-foreground">
            Published ontology graph for this workspace.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {data?.version ? (
            <>
              <Badge variant="default">v{data.version.version_number}</Badge>
              <span>{nodes.length} entities</span>
              <span>·</span>
              <span>{edges.length} relations</span>
              <span>·</span>
              <span>published {formatDateTime(data.version.created_at)}</span>
            </>
          ) : (
            <Badge variant="secondary">No published version</Badge>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="relative flex-1 bg-background">
          {isLoading && (
            <div className="p-6">
              <Skeleton className="h-[400px] w-full" />
            </div>
          )}
          {isError && (
            <div className="p-6 text-sm text-destructive">
              Failed to load graph: {(error as Error)?.message}
            </div>
          )}
          {!isLoading && !isError && nodes.length === 0 && (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              No entities published yet. Approve ontology candidates and
              publish a build to populate the graph.
            </div>
          )}
          {!isLoading && !isError && nodes.length > 0 && (
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              onSelect={handleSelect}
            />
          )}
        </div>
        <aside className="hidden w-80 shrink-0 overflow-y-auto border-l bg-muted/10 p-4 lg:block">
          <Inspector selection={selection} />
        </aside>
      </div>
    </div>
  );
}

function Inspector({ selection }: { selection: Selection }) {
  if (!selection) {
    return (
      <p className="text-sm text-muted-foreground">
        Click a node or edge to inspect its details.
      </p>
    );
  }
  if (selection.kind === "node") {
    const n = selection.node;
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">{n.name}</CardTitle>
          <Badge variant="outline" className="w-fit">
            {n.entityType}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-3 text-xs text-muted-foreground">
          {n.aliases.length > 0 && (
            <div>
              <div className="font-medium text-foreground">Aliases</div>
              <div>{n.aliases.join(", ")}</div>
            </div>
          )}
          <div>
            <div className="font-medium text-foreground">Source document</div>
            <div className="break-all font-mono">{n.sourceDocumentId}</div>
          </div>
        </CardContent>
      </Card>
    );
  }
  const { edge, source, target } = selection;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Relation</CardTitle>
        <Badge variant="outline" className="w-fit">
          {edge.relationType}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3 text-xs text-muted-foreground">
        <div>
          <div className="font-medium text-foreground">Source</div>
          <div>{source.name}</div>
        </div>
        <div>
          <div className="font-medium text-foreground">Target</div>
          <div>{target.name}</div>
        </div>
        <div>
          <div className="font-medium text-foreground">Confidence</div>
          <div>{Math.round(edge.confidence * 100)}%</div>
        </div>
        {edge.evidenceText && (
          <div>
            <div className="font-medium text-foreground">Evidence</div>
            <div className="whitespace-pre-wrap">{edge.evidenceText}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
