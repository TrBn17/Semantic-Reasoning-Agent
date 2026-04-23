"use client";

import { Card, CardContent } from "@/components/ui/card";

export function CrossBuildReview() {
  return (
    <Card>
      <CardContent className="p-6 text-sm text-muted-foreground">
        Cross-build candidate review is no longer available because ontology extraction results are
        no longer persisted as candidate rows in PostgreSQL. Use graph draft editing for curation.
      </CardContent>
    </Card>
  );
}
