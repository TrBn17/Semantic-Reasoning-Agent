import { BuildTable } from "@/components/ontology/build-table";
import { GraphStats } from "@/components/ontology/graph-stats";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";

export default function OntologyPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Ontology pipeline</h1>
          <p className="text-sm text-muted-foreground">
            Move from indexed documents to extracted candidates, review, and published graph versions.
          </p>
        </div>
        <NewBuildDialog />
      </div>
      <GraphStats />
      <div>
        <h2 className="mb-2 text-sm font-semibold">Recent builds</h2>
        <BuildTable limit={5} />
      </div>
    </div>
  );
}
