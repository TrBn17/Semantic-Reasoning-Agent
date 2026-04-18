import { getApiBaseUrl } from "../../../lib/api-base";

type OntologyBuild = {
  id: string;
  status: string;
  entity_count: number;
  relation_count: number;
  pending_entity_count: number;
  pending_relation_count: number;
};

async function fetchBuilds(): Promise<OntologyBuild[]> {
  const apiBase = getApiBaseUrl();
  const response = await fetch(`${apiBase}/ontology/builds`, { cache: "no-store" });
  if (!response.ok) {
    return [];
  }
  return (await response.json()) as OntologyBuild[];
}

export default async function OntologyBuildsPage() {
  const builds = await fetchBuilds();

  return (
    <main>
      <h1>Ontology Builds</h1>
      <p>Build monitor for Phase A pipeline runs.</p>
      <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(builds, null, 2)}</pre>
    </main>
  );
}
