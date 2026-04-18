import { getApiBaseUrl } from "../../lib/api-base";

async function fetchGraph() {
  const apiBase = getApiBaseUrl();
  const response = await fetch(`${apiBase}/ontology/graph`, { cache: "no-store" });
  if (!response.ok) {
    return { error: `Failed to load graph (${response.status})` };
  }
  return response.json();
}

export default async function OntologyPage() {
  const graph = await fetchGraph();
  const entities = Array.isArray((graph as { entities?: unknown[] }).entities)
    ? ((graph as { entities: unknown[] }).entities.length ?? 0)
    : 0;
  const relations = Array.isArray((graph as { relations?: unknown[] }).relations)
    ? ((graph as { relations: unknown[] }).relations.length ?? 0)
    : 0;

  return (
    <main>
      <h1>Ontology Dashboard</h1>
      <p>Phase A minimal read view for build/review flow.</p>
      {"error" in graph ? (
        <p>{graph.error}</p>
      ) : (
        <div>
          <p>Entities: {entities}</p>
          <p>Relations: {relations}</p>
          <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(graph, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}
