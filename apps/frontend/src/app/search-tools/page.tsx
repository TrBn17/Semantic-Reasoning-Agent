"use client";

import { SearchToolsView } from "@/components/search-tools/search-tools-view";

export default function SearchToolsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Search Tools</h1>
        <p className="text-sm text-muted-foreground">
          Create reusable super-search tools over documents or the ontology graph. Pick
          provider + model once, then invoke with a single click.
        </p>
      </div>
      <SearchToolsView />
    </div>
  );
}
