import { CrossBuildReview } from "@/components/ontology/cross-build-review";

export default function OntologyReviewPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div>
        <h1 className="text-xl font-semibold">Review queue</h1>
        <p className="text-sm text-muted-foreground">
          All pending candidates across builds in this workspace.
        </p>
      </div>
      <CrossBuildReview />
    </div>
  );
}
