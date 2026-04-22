"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  createDraftNode,
  createDraftRelation,
  deleteDraftNode,
  deleteDraftRelation,
  getGraph,
  getGraphDraft,
  previewPublish,
  publishDraft,
  resetDraft,
  updateDraftNode,
  updateDraftRelation,
} from "@/lib/api/ontology";
import { queryKeys } from "@/lib/query/keys";
import { useWorkspaceStore } from "@/lib/state/workspace-store";
import { formatDateTime } from "@/lib/utils";
import { entityToNode, relationToEdge } from "@/src/shared/api/adapters/ontology";
import { track } from "@/src/shared/telemetry/track";
import type {
  GraphEdgeViewModel,
  GraphNodeViewModel,
} from "@/src/entities/ontology/types";
import type { OntologyGraphDraftResponse, OntologyGraphResponse } from "@/lib/api/types";

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
  const queryClient = useQueryClient();
  const [selection, setSelection] = useState<Selection>(null);
  const [newNodeName, setNewNodeName] = useState("");
  const [newNodeType, setNewNodeType] = useState("");
  const [relationTargetId, setRelationTargetId] = useState("");
  const [relationType, setRelationType] = useState("");
  const [relationEvidence, setRelationEvidence] = useState("");

  const publishedGraph = useQuery({
    queryKey: queryKeys.ontology.graph(workspaceId ?? undefined),
    queryFn: () => getGraph(workspaceId ?? undefined),
  });
  const draftGraph = useQuery({
    queryKey: [...queryKeys.ontology.graph(workspaceId ?? undefined), "draft"],
    queryFn: () => getGraphDraft(workspaceId ?? undefined),
  });

  const invalidateOntology = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.all }),
      queryClient.invalidateQueries({ queryKey: queryKeys.ontology.graph(workspaceId ?? undefined) }),
    ]);
  };

  const addNodeMutation = useMutation({
    mutationFn: () =>
      createDraftNode(
        { name: newNodeName.trim(), entity_type: newNodeType.trim() },
        workspaceId ?? undefined,
      ),
    onSuccess: async () => {
      setNewNodeName("");
      setNewNodeType("");
      await invalidateOntology();
      toast.success("Draft node added");
    },
    onError: (error) => toast.error((error as Error).message),
  });

  const resetMutation = useMutation({
    mutationFn: () => resetDraft(workspaceId ?? undefined),
    onSuccess: async () => {
      await invalidateOntology();
      setSelection(null);
      toast.success("Draft reset");
    },
    onError: (error) => toast.error((error as Error).message),
  });

  const publishMutation = useMutation({
    mutationFn: async () => publishDraft({ workspace_id: workspaceId ?? undefined }),
    onSuccess: async () => {
      await invalidateOntology();
      toast.success("Draft published");
    },
    onError: (error) => toast.error((error as Error).message),
  });

  const graphData = draftGraph.data ?? publishedGraph.data;
  const nodes = useMemo(() => (graphData?.entities ?? []).map(entityToNode), [graphData?.entities]);
  const edges = useMemo(() => (graphData?.relations ?? []).map(relationToEdge), [graphData?.relations]);
  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  const handleSelect = (
    sel: { kind: "node"; node: GraphNodeViewModel } | { kind: "edge"; edge: GraphEdgeViewModel } | null,
  ) => {
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
    if (!source || !target) return;
    setSelection({ kind: "edge", edge: sel.edge, source, target });
  };

  const renameNode = async (node: GraphNodeViewModel) => {
    const nextName = window.prompt("Rename node", node.name);
    if (!nextName || nextName.trim() === node.name) return;
    await updateDraftNode(node.id, { name: nextName.trim() }, workspaceId ?? undefined);
    await invalidateOntology();
  };

  const renameEdge = async (edge: GraphEdgeViewModel) => {
    const nextType = window.prompt("Relation type", edge.relationType);
    if (!nextType || nextType.trim() === edge.relationType) return;
    await updateDraftRelation(edge.id, { relation_type: nextType.trim() }, workspaceId ?? undefined);
    await invalidateOntology();
  };

  const createRelationMutation = useMutation({
    mutationFn: async () => {
      if (selection?.kind !== "node") {
        throw new Error("Select a source node first.");
      }
      return createDraftRelation(
        {
          source_entity_id: selection.node.id,
          target_entity_id: relationTargetId,
          relation_type: relationType.trim(),
          evidence_text: relationEvidence.trim(),
        },
        workspaceId ?? undefined,
      );
    },
    onSuccess: async () => {
      setRelationTargetId("");
      setRelationType("");
      setRelationEvidence("");
      await invalidateOntology();
      toast.success("Draft relation added");
    },
    onError: (error) => toast.error((error as Error).message),
  });

  const draftSummary = draftGraph.data?.draft_summary ?? publishedGraph.data?.draft_summary;
  const ontologyTitle =
    draftGraph.data?.ontology_title ??
    publishedGraph.data?.ontology_title ??
    graphData?.version?.ontology_title ??
    "Workspace Ontology";
  const ontologySummary =
    draftGraph.data?.ontology_summary ??
    publishedGraph.data?.ontology_summary ??
    graphData?.version?.ontology_summary;

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.16),_transparent_35%),radial-gradient(circle_at_top_right,_rgba(34,197,94,0.12),_transparent_30%),linear-gradient(180deg,_rgba(15,23,42,0.03),_transparent_65%)]">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-6 px-6 py-6">
        <header className="rounded-3xl border bg-background/90 p-6 shadow-sm backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary">Graph Editor</Badge>
                {graphData?.version ? (
                  <Badge>v{graphData.version.version_number}</Badge>
                ) : (
                  <Badge variant="outline">Draft only</Badge>
                )}
                {draftSummary?.has_changes ? (
                  <Badge variant="outline">Draft changes pending</Badge>
                ) : null}
              </div>
              <div>
                <h1 className="font-serif text-3xl tracking-tight">{ontologyTitle}</h1>
                <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                  {ontologySummary || "Graph-first workspace editor. Changes stay in Postgres draft state until publish."}
                </p>
              </div>
            </div>
            <div className="grid min-w-[260px] gap-2 text-xs text-muted-foreground">
              <span>{nodes.length} entities</span>
              <span>{edges.length} relations</span>
              <span>Published {formatDateTime(graphData?.version?.created_at)}</span>
              <span>Draft updated {formatDateTime(draftSummary?.updated_at)}</span>
            </div>
          </div>
        </header>

        <div className="rounded-2xl border bg-background/95 p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <Input
              value={newNodeName}
              onChange={(event) => setNewNodeName(event.target.value)}
              placeholder="New node name"
              className="w-52"
            />
            <Input
              value={newNodeType}
              onChange={(event) => setNewNodeType(event.target.value)}
              placeholder="Entity type"
              className="w-40"
            />
            <Button
              onClick={() => addNodeMutation.mutate()}
              disabled={!newNodeName.trim() || !newNodeType.trim() || addNodeMutation.isPending}
            >
              Add Node
            </Button>
            <Button variant="outline" onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending}>
              Reset Draft
            </Button>
            <Button variant="secondary" onClick={() => publishMutation.mutate()} disabled={publishMutation.isPending}>
              Publish Draft
            </Button>
          </div>
        </div>

        {draftSummary?.has_changes ? (
          <DraftPreviewCard buildId={graphData?.version?.source_build_id ?? null} workspaceId={workspaceId ?? undefined} />
        ) : null}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="overflow-hidden rounded-[28px] border bg-background shadow-sm">
            <div className="flex items-center justify-between border-b px-6 py-4">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Canvas
                </h2>
                <p className="text-xs text-muted-foreground">
                  Double-click nodes or edges to rename inline through the draft API.
                </p>
              </div>
            </div>
            <div className="relative min-h-[720px] bg-[linear-gradient(0deg,rgba(148,163,184,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.08)_1px,transparent_1px)] bg-[size:28px_28px]">
              {draftGraph.isLoading && <div className="p-6"><Skeleton className="h-[640px] w-full" /></div>}
              {!draftGraph.isLoading && nodes.length === 0 ? (
                <div className="flex h-[720px] items-center justify-center text-sm text-muted-foreground">
                  No ontology nodes yet. Publish a build or start adding draft nodes.
                </div>
              ) : (
                <GraphCanvas
                  nodes={nodes}
                  edges={edges}
                  onSelect={handleSelect}
                  onNodeRename={renameNode}
                  onEdgeRename={renameEdge}
                />
              )}
            </div>
          </div>

          <div className="space-y-4">
            <Inspector
              selection={selection}
              nodes={nodes}
              relationTargetId={relationTargetId}
              relationType={relationType}
              relationEvidence={relationEvidence}
              onRelationTargetIdChange={setRelationTargetId}
              onRelationTypeChange={setRelationType}
              onRelationEvidenceChange={setRelationEvidence}
              onCreateRelation={() => createRelationMutation.mutate()}
              workspaceId={workspaceId ?? undefined}
              onInvalidate={invalidateOntology}
            />
            <SchemaPanel graph={graphData} />
          </div>
        </div>
      </div>
    </div>
  );
}

function DraftPreviewCard({ buildId, workspaceId }: { buildId: string | null; workspaceId?: string }) {
  const preview = useQuery({
    queryKey: ["ontology", "publish-preview", buildId, workspaceId ?? null],
    queryFn: () => previewPublish(buildId!),
    enabled: Boolean(buildId),
  });

  if (!buildId || preview.isLoading || !preview.data) return null;

  return (
    <Card className="border-amber-200 bg-amber-50/70">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Publish Preview</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-4 text-xs text-muted-foreground">
        <span>+{preview.data.diff_summary.entities_added ?? 0} entities</span>
        <span>~{preview.data.diff_summary.entities_updated ?? 0} updated entities</span>
        <span>+{preview.data.diff_summary.relations_added ?? 0} relations</span>
        <span>~{preview.data.diff_summary.relations_updated ?? 0} updated relations</span>
      </CardContent>
    </Card>
  );
}

function Inspector({
  selection,
  nodes,
  relationTargetId,
  relationType,
  relationEvidence,
  onRelationTargetIdChange,
  onRelationTypeChange,
  onRelationEvidenceChange,
  onCreateRelation,
  workspaceId,
  onInvalidate,
}: {
  selection: Selection;
  nodes: GraphNodeViewModel[];
  relationTargetId: string;
  relationType: string;
  relationEvidence: string;
  onRelationTargetIdChange: (value: string) => void;
  onRelationTypeChange: (value: string) => void;
  onRelationEvidenceChange: (value: string) => void;
  onCreateRelation: () => void;
  workspaceId?: string;
  onInvalidate: () => Promise<void>;
}) {
  const deleteNodeMutation = useMutation({
    mutationFn: (nodeId: string) => deleteDraftNode(nodeId, workspaceId),
    onSuccess: async () => {
      await onInvalidate();
      toast.success("Node removed from draft");
    },
    onError: (error) => toast.error((error as Error).message),
  });
  const deleteRelationMutation = useMutation({
    mutationFn: (relationId: string) => deleteDraftRelation(relationId, workspaceId),
    onSuccess: async () => {
      await onInvalidate();
      toast.success("Relation removed from draft");
    },
    onError: (error) => toast.error((error as Error).message),
  });

  if (!selection) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Inspector</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Select a node or edge on the canvas to inspect it, then edit through the draft API.
        </CardContent>
      </Card>
    );
  }

  if (selection.kind === "node") {
    const node = selection.node;
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">{node.name}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-muted-foreground">
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{node.entityType}</Badge>
            <Badge variant="secondary">{node.resolutionKey}</Badge>
          </div>
          <div>
            <div className="font-medium text-foreground">Aliases</div>
            <div>{node.aliases.length > 0 ? node.aliases.join(", ") : "No aliases"}</div>
          </div>
          <div>
            <div className="font-medium text-foreground">Source</div>
            <div>{node.sourceDocumentId}</div>
          </div>
          <div className="space-y-2 rounded-xl border bg-muted/30 p-3">
            <div className="font-medium text-foreground">Create relation from this node</div>
            <select
              value={relationTargetId}
              onChange={(event) => onRelationTargetIdChange(event.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="">Target node</option>
              {nodes
                .filter((candidate) => candidate.id !== node.id)
                .map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.name}
                  </option>
                ))}
            </select>
            <Input
              value={relationType}
              onChange={(event) => onRelationTypeChange(event.target.value)}
              placeholder="Relation type"
            />
            <Textarea
              value={relationEvidence}
              onChange={(event) => onRelationEvidenceChange(event.target.value)}
              placeholder="Evidence / rationale"
            />
            <Button
              onClick={onCreateRelation}
              disabled={!relationTargetId || !relationType.trim()}
              className="w-full"
            >
              Add Relation
            </Button>
          </div>
          <Button
            variant="destructive"
            className="w-full"
            onClick={() => deleteNodeMutation.mutate(node.id)}
            disabled={deleteNodeMutation.isPending}
          >
            Delete Node
          </Button>
        </CardContent>
      </Card>
    );
  }

  const { edge, source, target } = selection;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Relation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-xs text-muted-foreground">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline">{edge.relationType}</Badge>
          <Badge variant="secondary">{Math.round(edge.confidence * 100)}%</Badge>
        </div>
        <div>
          <div className="font-medium text-foreground">Source</div>
          <div>{source.name}</div>
        </div>
        <div>
          <div className="font-medium text-foreground">Target</div>
          <div>{target.name}</div>
        </div>
        {edge.evidenceText ? (
          <div>
            <div className="font-medium text-foreground">Evidence</div>
            <div className="whitespace-pre-wrap">{edge.evidenceText}</div>
          </div>
        ) : null}
        <Button
          variant="destructive"
          className="w-full"
          onClick={() => deleteRelationMutation.mutate(edge.id)}
          disabled={deleteRelationMutation.isPending}
        >
          Delete Relation
        </Button>
      </CardContent>
    </Card>
  );
}

function SchemaPanel({ graph }: { graph: OntologyGraphDraftResponse | OntologyGraphResponse | undefined }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Schema Surface</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-xs text-muted-foreground">
        <div>
          <div className="mb-2 font-medium text-foreground">Entity Types</div>
          <div className="flex flex-wrap gap-2">
            {(graph?.entity_type_definitions ?? []).map((item) => (
              <Badge key={item.id} variant="outline">
                {item.name}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <div className="mb-2 font-medium text-foreground">Relation Types</div>
          <div className="flex flex-wrap gap-2">
            {(graph?.relation_type_definitions ?? []).map((item) => (
              <Badge key={item.id} variant="outline">
                {item.name}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
