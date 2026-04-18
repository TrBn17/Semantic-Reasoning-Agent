import { getApiBaseUrl } from "../../../lib/api-base";

type CandidateEntity = {
  id: string;
  canonical_name: string;
  status: string;
};

async function fetchPendingEntities(): Promise<CandidateEntity[]> {
  const apiBase = getApiBaseUrl();
  const buildsResponse = await fetch(`${apiBase}/ontology/builds`, { cache: "no-store" });
  if (!buildsResponse.ok) {
    return [];
  }
  const builds = (await buildsResponse.json()) as Array<{ id: string }>;
  if (!builds.length) {
    return [];
  }
  const entitiesResponse = await fetch(
    `${apiBase}/ontology/builds/${builds[0].id}/entities?review_status=pending_review`,
    { cache: "no-store" }
  );
  if (!entitiesResponse.ok) {
    return [];
  }
  return (await entitiesResponse.json()) as CandidateEntity[];
}

export default async function OntologyReviewPage() {
  const entities = await fetchPendingEntities();

  return (
    <main>
      <h1>Ontology Review Queue</h1>
      <p>Pending entities from the latest build.</p>
      <pre style={{ whiteSpace: "pre-wrap" }}>{JSON.stringify(entities, null, 2)}</pre>
    </main>
  );
}
