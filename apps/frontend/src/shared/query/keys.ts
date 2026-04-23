export const queryKeys = {
  me: ["me"] as const,
  agents: {
    settings: (workspaceId?: string | null) =>
      ["agents", "settings", workspaceId ?? null] as const,
    profiles: (workspaceId?: string | null) =>
      ["agents", "profiles", workspaceId ?? null] as const,
  },
  conversations: {
    all: ["conversations"] as const,
    list: () => ["conversations", "list"] as const,
    detail: (id: string) => ["conversations", id] as const,
  },
  documents: {
    all: ["documents"] as const,
    list: () => ["documents", "list"] as const,
    detail: (id: string) => ["documents", id] as const,
    jobs: (id: string) => ["documents", id, "jobs"] as const,
    artifacts: (id: string) => ["documents", id, "artifacts"] as const,
  },
  retrieval: {
    search: (query: string, topK: number, documentIds: string[]) =>
      ["retrieval", "search", query, topK, [...documentIds].sort()] as const,
  },
  tools: {
    all: ["tools"] as const,
    list: () => ["tools", "list"] as const,
  },
  tasks: {
    all: ["tasks"] as const,
    list: () => ["tasks", "list"] as const,
    detail: (id: string) => ["tasks", id] as const,
    toolCalls: (id: string) => ["tasks", id, "tool-calls"] as const,
  },
  workflows: {
    all: ["workflows"] as const,
    list: () => ["workflows", "list"] as const,
    runs: () => ["workflows", "runs"] as const,
  },
  settings: {
    all: ["settings"] as const,
    bootstrap: (workspaceId?: string | null) =>
      ["settings", "bootstrap", workspaceId ?? null] as const,
    models: (workspaceId?: string | null) =>
      ["settings", "models", workspaceId ?? null] as const,
  },
  knowledgePacks: {
    all: ["knowledge-packs"] as const,
    list: (workspaceId?: string | null) =>
      ["knowledge-packs", "list", workspaceId ?? null] as const,
  },
  capabilities: {
    all: ["agent-capabilities"] as const,
    catalog: () => ["agent-capabilities", "catalog"] as const,
    tools: () => ["agent-capabilities", "tools"] as const,
  },
  searchTools: {
    all: ["search-tools"] as const,
    list: (workspaceId?: string | null, toolType?: string | null) =>
      ["search-tools", "list", workspaceId ?? null, toolType ?? "all"] as const,
    detail: (id: string) => ["search-tools", id] as const,
  },
  ontology: {
    all: ["ontology"] as const,
    graph: (workspaceId?: string) => ["ontology", "graph", workspaceId ?? null] as const,
    builds: (workspaceId?: string) =>
      ["ontology", "builds", workspaceId ?? null] as const,
    build: (id: string) => ["ontology", "builds", id] as const,
    buildEntities: (id: string, status?: string) =>
      ["ontology", "builds", id, "entities", status ?? "all"] as const,
    buildRelations: (id: string, status?: string) =>
      ["ontology", "builds", id, "relations", status ?? "all"] as const,
  },
};
