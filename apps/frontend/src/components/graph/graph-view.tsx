"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import Link from "next/link";
import {
  Eye,
  LayoutPanelTop,
  Maximize2,
  RefreshCcw,
  SplitSquareVertical,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Time } from "@/shared/components/time";
import { entityToNode, relationToEdge } from "@/shared/api/adapters/ontology";
import { getGraph } from "@/shared/api/ontology";
import { useI18n } from "@/shared/i18n/use-language";
import { queryKeys } from "@/shared/query/keys";
import { useWorkspaceStore } from "@/shared/state/workspace-store";
import type { GraphCanvasHandle } from "@/components/graph/graph-canvas";
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
  const { t } = useI18n();
  const workspaceId = useWorkspaceStore((state) => state.workspaceId);
  const canvasRef = useRef<GraphCanvasHandle | null>(null);
  const [mode, setMode] = useState<ViewMode>("split");
  const [search, setSearch] = useState("");
  /** Empty set = all entity types visible */
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(() => new Set());
  const [selection, setSelection] = useState<Selection>(null);
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });

  const nodes = useMemo(() => (data?.entities ?? []).map(entityToNode), [data?.entities]);
  const edges = useMemo(() => (data?.relations ?? []).map(relationToEdge), [data?.relations]);

  const toggleType = useCallback((typeName: string) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(typeName)) next.delete(typeName);
      else next.add(typeName);
      return next;
    });
  }, []);

  const clearTypeFilters = useCallback(() => {
    setSelectedTypes(new Set());
  }, []);

  const filteredNodes = useMemo(() => {
    return nodes.filter((node) => {
      if (selectedTypes.size > 0 && !selectedTypes.has(node.entityType)) return false;
      if (!search.trim()) return true;
      const q = search.trim().toLowerCase();
      return `${node.name} ${node.entityType} ${node.aliases.join(" ")}`.toLowerCase().includes(q);
    });
  }, [nodes, search, selectedTypes]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((node) => node.id)), [filteredNodes]);
  const filteredEdges = useMemo(
    () => edges.filter((edge) => filteredNodeIds.has(edge.sourceId) && filteredNodeIds.has(edge.targetId)),
    [edges, filteredNodeIds],
  );
  const nodeMap = useMemo(() => new Map(filteredNodes.map((node) => [node.id, node])), [filteredNodes]);
  const fullNodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);

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
      const source = fullNodeById.get(incoming.edge.sourceId);
      const target = fullNodeById.get(incoming.edge.targetId);
      if (source && target) {
        setSelection({ kind: "edge", edge: incoming.edge, source, target });
      }
    },
    [fullNodeById],
  );

  const focusNodeInCanvas = useCallback((nodeId: string) => {
    canvasRef.current?.centerOn(nodeId);
    const node = fullNodeById.get(nodeId);
    if (node) setSelection({ kind: "node", node });
  }, [fullNodeById]);

  const showGraph = mode === "graph" || mode === "split";
  const showInspector = mode === "inspector" || mode === "split";

  return (
    <div className="flex min-h-full min-w-0 flex-col bg-background">
      <header className="border-b bg-background/95 px-6 py-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex max-w-7xl flex-col gap-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">{t.graph.title}</h1>
              <p className="text-sm text-muted-foreground">{t.graph.subtitle}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <ModeButton
                active={mode === "graph"}
                onClick={() => setMode("graph")}
                icon={Eye}
                label={t.graph.modeGraphOnly}
              />
              <ModeButton
                active={mode === "split"}
                onClick={() => setMode("split")}
                icon={SplitSquareVertical}
                label={t.graph.modeSplit}
              />
              <ModeButton
                active={mode === "inspector"}
                onClick={() => setMode("inspector")}
                icon={LayoutPanelTop}
                label={t.graph.modeInspector}
              />
              <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
                <RefreshCcw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
                {t.graph.refresh}
              </Button>
              {showGraph && !isLoading && !isError && filteredNodes.length > 0 && (
                <>
                  <Button variant="outline" size="sm" type="button" onClick={() => canvasRef.current?.zoomIn()} title={t.graph.zoomIn}>
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" type="button" onClick={() => canvasRef.current?.zoomOut()} title={t.graph.zoomOut}>
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm" type="button" onClick={() => canvasRef.current?.fit()} title={t.graph.fitView}>
                    <Maximize2 className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {data?.version ? (
              <>
                <Badge>
                  {t.graph.versionBadge} {data.version.version_number}
                </Badge>
                <Badge variant="outline">
                  {nodes.length} {t.graph.entitiesBadge}
                </Badge>
                <Badge variant="outline">
                  {edges.length} {t.graph.relationsBadge}
                </Badge>
                <Badge variant="outline">
                  {t.graph.publishedPrefix}{" "}
                  <Time value={data.version.created_at} className="inline align-baseline" />
                </Badge>
                {data.graphiti_indexed ? (
                  <Badge variant="secondary">{t.graph.graphitiIndexed}</Badge>
                ) : null}
              </>
            ) : (
              <Badge variant="secondary">{t.graph.noPublishedGraph}</Badge>
            )}
            {typeCounts.slice(0, 6).map(([typeName, count]) => (
              <Badge key={typeName} variant="outline">
                {typeName}: {count}
              </Badge>
            ))}
          </div>
          <div className="flex flex-col gap-3">
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t.graph.searchNodesPlaceholder}
            />
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">{t.graph.filterTypesHint}:</span>
              <Button type="button" variant={selectedTypes.size === 0 ? "secondary" : "outline"} size="sm" onClick={clearTypeFilters}>
                {t.graph.allTypes}
              </Button>
              {typeCounts.map(([typeName]) => {
                const filtering = selectedTypes.size > 0;
                const included = selectedTypes.has(typeName);
                return (
                  <Button
                    key={typeName}
                    type="button"
                    size="sm"
                    variant={filtering && included ? "default" : "outline"}
                    className={`h-7 text-xs ${filtering && !included ? "opacity-50" : ""}`}
                    onClick={() => toggleType(typeName)}
                  >
                    {typeName}
                  </Button>
                );
              })}
              {selectedTypes.size > 0 && (
                <Button type="button" variant="ghost" size="sm" className="h-7 text-xs" onClick={clearTypeFilters}>
                  {t.graph.clearFilters}
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto flex min-h-0 w-full max-w-7xl flex-1 gap-4 overflow-hidden p-4">
        {showGraph && (
          <section className={`min-h-0 ${showInspector ? "flex-[1.35]" : "flex-1"}`}>
            <Card className="flex h-full min-h-0 flex-col overflow-hidden border shadow-md">
              <CardHeader className="border-b bg-card py-3">
                <CardTitle className="text-base">{t.graph.canvasTitle}</CardTitle>
              </CardHeader>
              <CardContent className="relative flex-1 bg-muted/20 p-0 dark:bg-muted/10">
                {isLoading && <Skeleton className="h-full w-full" />}
                {isError && (
                  <div className="p-6 text-sm text-destructive">
                    {t.graph.loadFailedPrefix} {(error as Error)?.message}
                  </div>
                )}
                {!isLoading && !isError && filteredNodes.length === 0 && (
                  <div className="flex h-full flex-col items-center justify-center gap-4 p-10 text-center text-sm text-muted-foreground">
                    <p>{t.graph.emptyState}</p>
                    <Button asChild variant="default" size="sm">
                      <Link href="/ontology/builds">{t.graph.emptyCta}</Link>
                    </Button>
                  </div>
                )}
                {!isLoading && !isError && filteredNodes.length > 0 && (
                  <GraphCanvas
                    ref={canvasRef}
                    nodes={filteredNodes}
                    edges={filteredEdges}
                    onSelect={handleSelect}
                  />
                )}
              </CardContent>
            </Card>
          </section>
        )}

        {showInspector && (
          <aside className={`${showGraph ? "w-[360px]" : "flex-1"} min-h-0`}>
            <div className="grid h-full min-h-0 gap-4 overflow-y-auto">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">{t.graph.legendTitle}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {typeCounts.length === 0 && (
                    <p className="text-muted-foreground">{t.graph.noEntityTypes}</p>
                  )}
                  {typeCounts.map(([typeName, count]) => (
                    <div key={typeName} className="flex items-center justify-between rounded-xl border px-3 py-2">
                      <span className="font-medium">{typeName}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Inspector
                selection={selection}
                allNodes={nodes}
                allEdges={edges}
                onFocusNode={focusNodeInCanvas}
                labels={{
                  title: t.graph.inspectorTitle,
                  empty: t.graph.inspectorEmpty,
                  aliases: t.graph.aliasesLabel,
                  noAliases: t.graph.noAliases,
                  sourceDoc: t.graph.sourceDocumentLabel,
                  connected: t.graph.connectedEdges,
                  outgoing: t.graph.outgoing,
                  incoming: t.graph.incoming,
                  selectNode: t.graph.selectNode,
                  relationSource: t.graph.relationSource,
                  relationTarget: t.graph.relationTarget,
                  confidence: t.graph.confidenceLabel,
                  evidence: t.graph.evidenceLabel,
                  noEvidence: t.graph.noEvidence,
                }}
              />
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

type InspectorLabels = {
  title: string;
  empty: string;
  aliases: string;
  noAliases: string;
  sourceDoc: string;
  connected: string;
  outgoing: string;
  incoming: string;
  selectNode: string;
  relationSource: string;
  relationTarget: string;
  confidence: string;
  evidence: string;
  noEvidence: string;
};

function Inspector({
  selection,
  allNodes,
  allEdges,
  onFocusNode,
  labels,
}: {
  selection: Selection;
  allNodes: GraphNodeViewModel[];
  allEdges: GraphEdgeViewModel[];
  onFocusNode: (id: string) => void;
  labels: InspectorLabels;
}) {
  if (!selection) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{labels.title}</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">{labels.empty}</CardContent>
      </Card>
    );
  }

  if (selection.kind === "node") {
    const outgoing = allEdges.filter((e) => e.sourceId === selection.node.id);
    const incoming = allEdges.filter((e) => e.targetId === selection.node.id);
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{selection.node.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Badge variant="outline">{selection.node.entityType}</Badge>
          <div>
            <div className="mb-1 text-xs uppercase text-muted-foreground">{labels.aliases}</div>
            <div>{selection.node.aliases.length > 0 ? selection.node.aliases.join(", ") : labels.noAliases}</div>
          </div>
          <div>
            <div className="mb-1 text-xs uppercase text-muted-foreground">{labels.sourceDoc}</div>
            <div className="break-all rounded-lg bg-muted/40 px-3 py-2 font-mono text-xs">
              {selection.node.sourceDocumentId}
            </div>
          </div>
          <div>
            <div className="mb-1 text-xs uppercase text-muted-foreground">{labels.connected}</div>
            <div className="mb-2 text-xs font-medium text-muted-foreground">{labels.outgoing}</div>
            <ul className="mb-3 space-y-1">
              {outgoing.map((e) => {
                const target = allNodes.find((n) => n.id === e.targetId);
                return (
                  <li key={e.id} className="flex flex-wrap items-center gap-2 rounded-md border px-2 py-1.5 text-xs">
                    <span className="font-medium">{e.relationType}</span>
                    <span className="text-muted-foreground">→ {target?.name ?? e.targetId}</span>
                    <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => onFocusNode(e.targetId)}>
                      {labels.selectNode}
                    </Button>
                  </li>
                );
              })}
              {outgoing.length === 0 && <li className="text-xs text-muted-foreground">—</li>}
            </ul>
            <div className="mb-2 text-xs font-medium text-muted-foreground">{labels.incoming}</div>
            <ul className="space-y-1">
              {incoming.map((e) => {
                const source = allNodes.find((n) => n.id === e.sourceId);
                return (
                  <li key={e.id} className="flex flex-wrap items-center gap-2 rounded-md border px-2 py-1.5 text-xs">
                    <span className="font-medium">{e.relationType}</span>
                    <span className="text-muted-foreground">← {source?.name ?? e.sourceId}</span>
                    <Button type="button" variant="ghost" size="sm" className="h-7 px-2 text-xs" onClick={() => onFocusNode(e.sourceId)}>
                      {labels.selectNode}
                    </Button>
                  </li>
                );
              })}
              {incoming.length === 0 && <li className="text-xs text-muted-foreground">—</li>}
            </ul>
          </div>
        </CardContent>
      </Card>
    );
  }

  const confPct = Math.round(selection.edge.confidence * 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{selection.edge.relationType}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="grid gap-3 md:grid-cols-2">
          <button
            type="button"
            className="rounded-xl border px-3 py-2 text-left transition-colors hover:bg-accent"
            onClick={() => onFocusNode(selection.source.id)}
          >
            <div className="text-xs uppercase text-muted-foreground">{labels.relationSource}</div>
            <div className="font-medium">{selection.source.name}</div>
            <div className="mt-1 text-xs text-primary">{labels.selectNode}</div>
          </button>
          <button
            type="button"
            className="rounded-xl border px-3 py-2 text-left transition-colors hover:bg-accent"
            onClick={() => onFocusNode(selection.target.id)}
          >
            <div className="text-xs uppercase text-muted-foreground">{labels.relationTarget}</div>
            <div className="font-medium">{selection.target.name}</div>
            <div className="mt-1 text-xs text-primary">{labels.selectNode}</div>
          </button>
        </div>
        <div>
          <div className="mb-1 text-xs uppercase text-muted-foreground">{labels.confidence}</div>
          <div className="flex items-center gap-2">
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <div className="h-full bg-primary transition-all" style={{ width: `${confPct}%` }} />
            </div>
            <span className="tabular-nums">{confPct}%</span>
          </div>
        </div>
        <div>
          <div className="mb-1 text-xs uppercase text-muted-foreground">{labels.evidence}</div>
          <div className="rounded-xl bg-muted/30 px-3 py-3 whitespace-pre-wrap">
            {selection.edge.evidenceText || labels.noEvidence}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
