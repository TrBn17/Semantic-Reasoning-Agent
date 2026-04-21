"use client";

import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { Eye, LayoutPanelTop, RefreshCcw, SplitSquareVertical } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getGraph } from "@/shared/api/ontology";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import { formatDateTime } from "@/shared/utils";
import { entityToNode, relationToEdge } from "@/shared/api/adapters/ontology";
import type { GraphEdgeViewModel, GraphNodeViewModel } from "@/entities/ontology/types";

const GraphCanvas = dynamic(
  () =>
    import("@/components/graph/graph-canvas").then((module) => ({
      default: module.GraphCanvas,
    })),
  { ssr: false, loading: () => <Skeleton className="h-full min-h-[400px] w-full" /> },
);

type ViewMode = "graph" | "split" | "inspector";
type Selection =
  | { kind: "node"; node: GraphNodeViewModel }
  | { kind: "edge"; edge: GraphEdgeViewModel; source: GraphNodeViewModel; target: GraphNodeViewModel }
  | null;

export function GraphView() {
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const [mode, setMode] = useState<ViewMode>("split");
  const [selection, setSelection] = useState<Selection>(null);
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });

  const nodes = useMemo(() => (data?.entities ?? []).map(entityToNode), [data?.entities]);
  const edges = useMemo(() => (data?.relations ?? []).map(relationToEdge), [data?.relations]);
  const nodeMap = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const typeCounts = useMemo(() => {
    const counts = new Map<string, number>();
    nodes.forEach((node) => counts.set(node.entityType, (counts.get(node.entityType) ?? 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [nodes]);

  const handleSelect = useCallback(
    (incoming: { kind: "node"; node: GraphNodeViewModel } | { kind: "edge"; edge: GraphEdgeViewModel } | null) => {
      if (!incoming) {
        setSelection(null);
        return;
      }
      if (incoming.kind === "node") {
        setSelection({ kind: "node", node: incoming.node });
        return;
      }
      const source = nodeMap.get(incoming.edge.sourceId);
      const target = nodeMap.get(incoming.edge.targetId);
      if (source && target) {
        setSelection({ kind: "edge", edge: incoming.edge, source, target });
      }
    },
    [nodeMap],
  );

  const showGraph = mode === "graph" || mode === "split";
  const showInspector = mode === "inspector" || mode === "split";

  return (
    <div className="flex h-full flex-col bg-[radial-gradient(circle_at_top_left,_rgba(58,130,107,0.18),_transparent_42%),linear-gradient(180deg,#f5efe4,#fbfaf6)]">
      <header className="border-b bg-background/70 px-6 py-4 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">Graph workbench</h1>
              <p className="text-sm text-muted-foreground">
                Published ontology, schema mix, and evidence-backed relation inspection.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <ModeButton active={mode === "graph"} onClick={() => setMode("graph")} icon={Eye} label="Graph only" />
              <ModeButton active={mode === "split"} onClick={() => setMode("split")} icon={SplitSquareVertical} label="Split view" />
              <ModeButton active={mode === "inspector"} onClick={() => setMode("inspector")} icon={LayoutPanelTop} label="Inspector" />
              <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
                <RefreshCcw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {data?.version ? (
              <>
                <Badge>Version {data.version.version_number}</Badge>
                <Badge variant="outline">{nodes.length} entities</Badge>
                <Badge variant="outline">{edges.length} relations</Badge>
                <Badge variant="outline">Published {formatDateTime(data.version.created_at)}</Badge>
              </>
            ) : (
              <Badge variant="secondary">No published graph</Badge>
            )}
            {typeCounts.slice(0, 4).map(([typeName, count]) => (
              <Badge key={typeName} variant="outline">
                {typeName}: {count}
              </Badge>
            ))}
          </div>
        </div>
      </header>

      <div className="mx-auto flex h-full w-full max-w-7xl flex-1 gap-4 overflow-hidden p-4">
        {showGraph && (
          <section className={`min-h-0 ${showInspector ? "flex-[1.35]" : "flex-1"}`}>
            <Card className="flex h-full min-h-[540px] flex-col overflow-hidden border-0 shadow-xl">
              <CardHeader className="border-b bg-slate-950 text-slate-100">
                <CardTitle className="text-base">Canvas</CardTitle>
              </CardHeader>
              <CardContent className="relative flex-1 bg-[linear-gradient(180deg,rgba(15,23,42,0.96),rgba(17,24,39,0.92))] p-0">
                {isLoading && <Skeleton className="h-full min-h-[400px] w-full" />}
                {isError && (
                  <div className="p-6 text-sm text-red-200">
                    Failed to load graph: {(error as Error)?.message}
                  </div>
                )}
                {!isLoading && !isError && nodes.length === 0 && (
                  <div className="flex h-full items-center justify-center p-10 text-center text-sm text-slate-300">
                    No published ontology version yet. Approve a build, publish it, then reopen the graph.
                  </div>
                )}
                {!isLoading && !isError && nodes.length > 0 && (
                  <GraphCanvas nodes={nodes} edges={edges} onSelect={handleSelect} />
                )}
              </CardContent>
            </Card>
          </section>
        )}

        {showInspector && (
          <aside className={`${showGraph ? "w-[360px]" : "flex-1"} min-h-0`}>
            <div className="grid h-full gap-4 overflow-y-auto">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Legend</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {typeCounts.length === 0 && (
                    <p className="text-muted-foreground">No entity types available yet.</p>
                  )}
                  {typeCounts.map(([typeName, count]) => (
                    <div key={typeName} className="flex items-center justify-between rounded-xl border px-3 py-2">
                      <span className="font-medium">{typeName}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Inspector selection={selection} />
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

function ModeButton({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Eye;
  label: string;
}) {
  return (
    <Button variant={active ? "default" : "outline"} size="sm" onClick={onClick}>
      <Icon className="h-4 w-4" />
      {label}
    </Button>
  );
}

function Inspector({ selection }: { selection: Selection }) {
  if (!selection) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Inspector</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Select a node or relation to inspect evidence, aliases, and connection context.
        </CardContent>
      </Card>
    );
  }

  if (selection.kind === "node") {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{selection.node.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Badge variant="outline">{selection.node.entityType}</Badge>
          <div>
            <div className="mb-1 text-xs uppercase text-muted-foreground">Aliases</div>
            <div>{selection.node.aliases.length > 0 ? selection.node.aliases.join(", ") : "No aliases recorded"}</div>
          </div>
          <div>
            <div className="mb-1 text-xs uppercase text-muted-foreground">Source document</div>
            <div className="break-all rounded-lg bg-muted/40 px-3 py-2 font-mono text-xs">
              {selection.node.sourceDocumentId}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{selection.edge.relationType}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border px-3 py-2">
            <div className="text-xs uppercase text-muted-foreground">Source</div>
            <div className="font-medium">{selection.source.name}</div>
          </div>
          <div className="rounded-xl border px-3 py-2">
            <div className="text-xs uppercase text-muted-foreground">Target</div>
            <div className="font-medium">{selection.target.name}</div>
          </div>
        </div>
        <div>
          <div className="mb-1 text-xs uppercase text-muted-foreground">Confidence</div>
          <div>{Math.round(selection.edge.confidence * 100)}%</div>
        </div>
        <div>
          <div className="mb-1 text-xs uppercase text-muted-foreground">Evidence</div>
          <div className="rounded-xl bg-muted/30 px-3 py-3 whitespace-pre-wrap">
            {selection.edge.evidenceText || "No evidence snippet stored"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
