import { BuildTable } from "@/components/ontology/build-table";
import { NewBuildDialog } from "@/components/ontology/new-build-dialog";

export default function OntologyBuildsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Ontology builds</h1>
          <p className="text-sm text-muted-foreground">
            Each build extracts candidate entities and relations from one
            document. Review and publish to promote them into the graph.
          </p>
        </div>
        <NewBuildDialog />
      </div>
      <BuildTable />
    </div>
  );
}
