import { BuildTable } from "@/components/ontology/build-table";
import { GraphStats } from "@/components/ontology/graph-stats";

export default function OntologyPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Ontology</h1>
        <p className="text-sm text-muted-foreground">
          Published graph summary and the 5 most recent builds.
        </p>
      </div>
      <GraphStats />
      <div>
        <h2 className="mb-2 text-sm font-semibold">Recent builds</h2>
        <BuildTable limit={5} />
      </div>
    </div>
  );
}
