"use client";

import { CrossBuildReview } from "@/components/ontology/cross-build-review";
import { useI18n } from "@/shared/i18n/use-language";

export default function OntologyReviewPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-4 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t.pages.ontologyReview.title}</h1>
      </div>
      <CrossBuildReview />
    </div>
  );
}
