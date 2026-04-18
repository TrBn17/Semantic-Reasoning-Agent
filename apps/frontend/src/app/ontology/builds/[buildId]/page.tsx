import { BuildDetail } from "@/components/ontology/build-detail";

export default async function BuildDetailPage({
  params,
}: {
  params: Promise<{ buildId: string }>;
}) {
  const { buildId } = await params;
  return (
    <div className="mx-auto max-w-6xl p-6">
      <BuildDetail buildId={buildId} />
    </div>
  );
}
