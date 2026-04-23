"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Loader2, Play, Plus, Trash2 } from "lucide-react";

import { ModelCombobox } from "@/components/agents/model-combobox";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  createSearchTool,
  deleteSearchTool,
  duplicateSearchTool,
  listSearchTools,
  runSearchTool,
} from "@/shared/api/search-tools";
import { listSettingsModels } from "@/shared/api/settings";
import { listDocuments } from "@/shared/api/documents";
import { queryKeys } from "@/shared/query/keys";
import type {
  DocumentResponse,
  Evidence,
  SearchFusionStrategy,
  SearchToolConfigCreateRequest,
  SearchToolConfigResponse,
  SearchToolRunResponse,
  SearchToolType,
  SettingsModelOption,
} from "@/shared/api/types";
import { parseModelValue } from "@/shared/utils/model-value";

export function SearchToolsView() {
  const [tab, setTab] = useState<SearchToolType>("docs");
  return (
    <Tabs value={tab} onValueChange={(v) => setTab(v as SearchToolType)} className="space-y-4">
      <TabsList>
        <TabsTrigger value="docs">Document Search</TabsTrigger>
        <TabsTrigger value="graph">Graph Search</TabsTrigger>
      </TabsList>
      <TabsContent value="docs" className="space-y-4">
        <SearchToolSection toolType="docs" />
      </TabsContent>
      <TabsContent value="graph" className="space-y-4">
        <SearchToolSection toolType="graph" />
      </TabsContent>
    </Tabs>
  );
}

function SearchToolSection({ toolType }: { toolType: SearchToolType }) {
  const query = useQuery({
    queryKey: queryKeys.searchTools.list(null, toolType),
    queryFn: () => listSearchTools({ toolType }),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {toolType === "docs"
            ? "Semantic + optional BM25 retrieval across a Qdrant collection or selected documents."
            : "Ontology graph search — published snapshot or a specific version, with configurable reranker."}
        </div>
        <CreateToolDialog toolType={toolType} />
      </div>

      {query.isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : query.isError ? (
        <p className="text-sm text-destructive">
          Failed to load configurations: {(query.error as Error)?.message}
        </p>
      ) : (query.data ?? []).length === 0 ? (
        <p className="rounded-md border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
          No saved {toolType === "docs" ? "document" : "graph"} search tools yet. Click{" "}
          <span className="font-medium">New tool</span> to create one.
        </p>
      ) : (
        <div className="grid gap-3">
          {(query.data ?? []).map((config) => (
            <SearchToolCard key={config.id} config={config} />
          ))}
        </div>
      )}
    </div>
  );
}

function SearchToolCard({ config }: { config: SearchToolConfigResponse }) {
  const qc = useQueryClient();
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchToolRunResponse | null>(null);

  const runMutation = useMutation({
    mutationFn: () => runSearchTool(config.id, { query }),
    onSuccess: (data) => setResult(data),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteSearchTool(config.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.searchTools.all });
    },
  });
  const duplicateMutation = useMutation({
    mutationFn: () => duplicateSearchTool(config.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.searchTools.all });
    },
  });

  return (
    <div className="rounded-xl border bg-background p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-semibold">{config.name}</h3>
            <Badge variant="outline" className="font-mono text-[10px]">
              {config.tool_type}
            </Badge>
            {config.is_system ? (
              <Badge variant="secondary" className="text-[10px]">
                system
              </Badge>
            ) : null}
            <Badge variant={config.ready ? "success" : "warning"} className="text-[10px]">
              {config.ready ? "ready" : "blocked"}
            </Badge>
          </div>
          {config.description ? (
            <p className="mt-1 text-xs text-muted-foreground">{config.description}</p>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-muted-foreground">
            <span className="rounded bg-muted px-1.5 py-0.5 font-mono">
              {config.embedding_provider}::{config.embedding_model}
            </span>
            <span className="rounded bg-muted px-1.5 py-0.5">top_k={config.default_top_k}</span>
            {config.tool_type === "docs" ? (
              <>
                <span className="rounded bg-muted px-1.5 py-0.5">
                  target={config.collection_target}
                  {config.collection_target === "documents"
                    ? ` (${config.document_ids.length})`
                    : ""}
                </span>
                <span className="rounded bg-muted px-1.5 py-0.5">
                  bm25={config.bm25_enabled ? "on" : "off"}
                </span>
                <span className="rounded bg-muted px-1.5 py-0.5">
                  fusion={config.fusion_strategy}
                </span>
              </>
            ) : (
              <>
                <span className="rounded bg-muted px-1.5 py-0.5">scope={config.ontology_scope}</span>
                <span className="rounded bg-muted px-1.5 py-0.5">
                  search_type={config.graph_search_type}
                </span>
                <span className="rounded bg-muted px-1.5 py-0.5">reranker={config.reranker}</span>
              </>
            )}
          </div>
          {!config.ready && config.ready_reason ? (
            <p className="mt-2 text-xs text-amber-700">{config.ready_reason}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => duplicateMutation.mutate()}
            disabled={duplicateMutation.isPending}
            aria-label="Duplicate tool"
          >
            <Copy className="h-4 w-4" />
          </Button>
          {!config.is_system ? (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => {
                if (confirm(`Delete "${config.name}"?`)) deleteMutation.mutate();
              }}
              disabled={deleteMutation.isPending}
              aria-label="Delete tool"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          ) : null}
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a query and press Run…"
          className="flex-1"
        />
        <Button
          type="button"
          onClick={() => runMutation.mutate()}
          disabled={!query.trim() || runMutation.isPending}
        >
          {runMutation.isPending ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Play className="mr-1 h-4 w-4" />
          )}
          Run
        </Button>
      </div>

      {runMutation.isError ? (
        <p className="mt-2 text-xs text-destructive">
          {(runMutation.error as Error)?.message}
        </p>
      ) : null}

      {result ? <RunResult result={result} /> : null}
    </div>
  );
}

function RunResult({ result }: { result: SearchToolRunResponse }) {
  return (
    <div className="mt-3 space-y-2 rounded-md border bg-muted/10 p-3">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <Badge variant={result.status === "success" ? "success" : result.status === "partial" ? "warning" : "destructive"}>
          {result.status}
        </Badge>
        <span>{result.evidence.length} hits</span>
        <span>· {result.latency_ms} ms</span>
        {result.error_message ? (
          <span className="text-destructive">· {result.error_message}</span>
        ) : null}
      </div>
      {result.next_action_hints.length > 0 ? (
        <div className="text-[11px] text-muted-foreground">
          Hints: {result.next_action_hints.join(" · ")}
        </div>
      ) : null}
      <div className="space-y-1.5">
        {result.evidence.map((ev) => (
          <EvidenceRow key={ev.evidence_id} ev={ev} />
        ))}
      </div>
    </div>
  );
}

function EvidenceRow({ ev }: { ev: Evidence }) {
  return (
    <div className="rounded border bg-background px-3 py-2 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono text-[10px]">
          {ev.source_type}
        </Badge>
        <span className="truncate font-medium">{ev.title}</span>
        <span className="ml-auto text-[10px] text-muted-foreground">score={ev.score.toFixed(3)}</span>
      </div>
      <p className="mt-1 line-clamp-3 text-muted-foreground">{ev.content}</p>
    </div>
  );
}

type DraftState = SearchToolConfigCreateRequest & {
  modelValue: string;
};

function emptyDraft(toolType: SearchToolType): DraftState {
  return {
    tool_type: toolType,
    name: "",
    description: "",
    provider: "",
    model: "",
    default_top_k: 5,
    collection_target: "workspace",
    document_ids: [],
    bm25_enabled: false,
    fusion_strategy: "semantic_only",
    ontology_scope: "published",
    ontology_version_id: null,
    graph_search_type: "combined",
    reranker: "rrf",
    config_metadata: {},
    modelValue: "",
  };
}

function CreateToolDialog({ toolType }: { toolType: SearchToolType }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<DraftState>(() => emptyDraft(toolType));

  const modelsQuery = useQuery({
    queryKey: queryKeys.settings.models(null),
    queryFn: () => listSettingsModels(null),
    enabled: open,
  });

  const documentsQuery = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: () => listDocuments(),
    enabled: open && toolType === "docs",
  });

  const createMutation = useMutation({
    mutationFn: (payload: SearchToolConfigCreateRequest) => createSearchTool(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.searchTools.all });
      setOpen(false);
      setDraft(emptyDraft(toolType));
    },
  });

  const canSubmit =
    draft.name.trim().length > 0 &&
    (toolType !== "docs" ||
      draft.collection_target === "workspace" ||
      (draft.document_ids?.length ?? 0) > 0);

  const submit = () => {
    const { modelValue: _modelValue, ...payload } = draft;
    createMutation.mutate(payload);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) setDraft(emptyDraft(toolType));
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="mr-1 h-4 w-4" /> New tool
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            New {toolType === "docs" ? "document" : "graph"} search tool
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <Field label="Name">
            <Input
              value={draft.name}
              onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
              placeholder="e.g. Delivery ops retrieval"
            />
          </Field>
          <Field label="Description" hint="Shown on the tool card.">
            <Textarea
              value={draft.description ?? ""}
              onChange={(e) => setDraft((d) => ({ ...d, description: e.target.value }))}
              rows={2}
            />
          </Field>

          <Field
            label="Legacy provider + model"
            hint="Optional compatibility fields. If omitted, workspace embedding defaults are used."
          >
            <ModelCombobox
              models={modelsQuery.data ?? ([] as SettingsModelOption[])}
              value={draft.modelValue}
              onChange={(value) => {
                const parsed = parseModelValue(value);
                setDraft((d) => ({
                  ...d,
                  modelValue: value,
                  provider: parsed?.provider ?? "",
                  model: parsed?.model ?? "",
                }));
              }}
              collapseOnSelect
            />
          </Field>

          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Embedding provider" hint="Defaults to the workspace search embedding provider.">
              <Input
                value={draft.embedding_provider ?? ""}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, embedding_provider: e.target.value }))
                }
                placeholder="cloudflare"
              />
            </Field>
            <Field label="Embedding model" hint="Defaults to the workspace search embedding model.">
              <Input
                value={draft.embedding_model ?? ""}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, embedding_model: e.target.value }))
                }
                placeholder="@cf/baai/bge-base-en-v1.5"
              />
            </Field>
          </div>

          <Field label="Default top_k">
            <Input
              type="number"
              min={1}
              max={50}
              value={draft.default_top_k ?? 5}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  default_top_k: Math.max(1, Math.min(50, Number(e.target.value) || 1)),
                }))
              }
            />
          </Field>

          {toolType === "docs" ? (
            <DocsFields
              draft={draft}
              setDraft={setDraft}
              documents={documentsQuery.data ?? []}
            />
          ) : (
            <GraphFields draft={draft} setDraft={setDraft} />
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button type="button" onClick={submit} disabled={!canSubmit || createMutation.isPending}>
            {createMutation.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : null}
            Create
          </Button>
        </DialogFooter>

        {createMutation.isError ? (
          <p className="text-xs text-destructive">
            {(createMutation.error as Error)?.message}
          </p>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function DocsFields({
  draft,
  setDraft,
  documents,
}: {
  draft: DraftState;
  setDraft: React.Dispatch<React.SetStateAction<DraftState>>;
  documents: DocumentResponse[];
}) {
  const docIds = useMemo(() => new Set(draft.document_ids ?? []), [draft.document_ids]);

  return (
    <>
      <Field label="Collection target">
        <Select
          value={draft.collection_target}
          onValueChange={(v) =>
            setDraft((d) => ({
              ...d,
              collection_target: v as DraftState["collection_target"],
              document_ids: v === "workspace" ? [] : d.document_ids,
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="workspace">Whole workspace</SelectItem>
            <SelectItem value="documents">Selected documents</SelectItem>
          </SelectContent>
        </Select>
      </Field>

      {draft.collection_target === "documents" ? (
        <Field label="Documents" hint="Pick one or more indexed documents to scope this tool.">
          <div className="max-h-48 overflow-y-auto rounded-md border">
            {documents.length === 0 ? (
              <p className="p-3 text-xs text-muted-foreground">No documents yet.</p>
            ) : (
              documents.map((doc) => {
                const checked = docIds.has(doc.id);
                return (
                  <label
                    key={doc.id}
                    className="flex cursor-pointer items-center gap-2 border-b px-2 py-1.5 text-xs last:border-b-0 hover:bg-muted/30"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        setDraft((d) => {
                          const next = new Set(d.document_ids ?? []);
                          if (e.target.checked) next.add(doc.id);
                          else next.delete(doc.id);
                          return { ...d, document_ids: Array.from(next) };
                        });
                      }}
                    />
                    <span className="truncate">{doc.title || doc.filename}</span>
                    <Badge variant="outline" className="ml-auto text-[10px]">
                      {doc.status}
                    </Badge>
                  </label>
                );
              })
            )}
          </div>
        </Field>
      ) : null}

      <Field label="BM25" hint="Toggle keyword scoring alongside semantic search.">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.bm25_enabled ?? false}
            onChange={(e) =>
              setDraft((d) => ({
                ...d,
                bm25_enabled: e.target.checked,
                fusion_strategy: e.target.checked
                  ? d.fusion_strategy === "semantic_only"
                    ? "hybrid_rrf"
                    : d.fusion_strategy
                  : "semantic_only",
              }))
            }
          />
          Enable BM25
        </label>
      </Field>

      <Field label="Fusion strategy">
        <Select
          value={draft.fusion_strategy}
          onValueChange={(v) =>
            setDraft((d) => ({
              ...d,
              fusion_strategy: v as SearchFusionStrategy,
              bm25_enabled:
                v === "semantic_only" ? false : v === "bm25_only" ? true : d.bm25_enabled,
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="semantic_only">Semantic only</SelectItem>
            <SelectItem value="bm25_only">BM25 only</SelectItem>
            <SelectItem value="hybrid_rrf">Hybrid (Semantic + BM25, RRF)</SelectItem>
          </SelectContent>
        </Select>
      </Field>
    </>
  );
}

function GraphFields({
  draft,
  setDraft,
}: {
  draft: DraftState;
  setDraft: React.Dispatch<React.SetStateAction<DraftState>>;
}) {
  return (
    <>
      <Field label="Ontology scope">
        <Select
          value={draft.ontology_scope}
          onValueChange={(v) =>
            setDraft((d) => ({
              ...d,
              ontology_scope: v as DraftState["ontology_scope"],
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="published">Published snapshot (default)</SelectItem>
            <SelectItem value="version">Specific version</SelectItem>
          </SelectContent>
        </Select>
      </Field>

      {draft.ontology_scope === "version" ? (
        <Field label="Ontology version id" hint="Paste the ontology_version_id to target.">
          <Input
            value={draft.ontology_version_id ?? ""}
            onChange={(e) =>
              setDraft((d) => ({
                ...d,
                ontology_version_id: e.target.value.trim() || null,
              }))
            }
          />
        </Field>
      ) : null}

      <Field label="Graph search type">
        <Select
          value={draft.graph_search_type}
          onValueChange={(v) =>
            setDraft((d) => ({
              ...d,
              graph_search_type: v as DraftState["graph_search_type"],
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="combined">Combined (nodes + edges)</SelectItem>
            <SelectItem value="nodes">Nodes</SelectItem>
            <SelectItem value="edges">Edges</SelectItem>
          </SelectContent>
        </Select>
      </Field>

      <Field label="Reranker">
        <Select
          value={draft.reranker}
          onValueChange={(v) =>
            setDraft((d) => ({
              ...d,
              reranker: v as DraftState["reranker"],
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="rrf">RRF (light, no extra model)</SelectItem>
            <SelectItem value="cross_encoder">Cross-encoder</SelectItem>
            <SelectItem value="none">None</SelectItem>
          </SelectContent>
        </Select>
      </Field>
    </>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      {children}
      {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
