import { BuildTable } from "@/components/ontology/build-table";
import { GraphStats } from "@/components/ontology/graph-stats";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function OntologyPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="rounded-3xl border bg-background p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold">Ontology Control Plane</h1>
            <p className="text-sm text-muted-foreground">
              Review builds, inspect the current published graph, and jump into the graph editor for draft-first changes.
            </p>
          </div>
          <Button asChild>
            <Link href="/graph">Open Graph Editor</Link>
          </Button>
        </div>
      </div>
      <div>
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
