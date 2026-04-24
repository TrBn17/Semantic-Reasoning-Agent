import { BuildDetail } from "@/components/ontology/build-detail";

export default async function BuildDetailPage({
  params,
}: {
  params: Promise<{ buildId: string }>;
}) {
  const { buildId } = await params;
  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 py-4 sm:px-6 lg:px-8">
      <section className="overflow-hidden rounded-2xl border bg-card shadow-sm lg:aspect-video lg:max-h-[calc(100vh-7.5rem)]">
        <div className="h-full min-h-0 overflow-y-auto p-4 sm:p-5">
          <BuildDetail buildId={buildId} />
        </div>
      </section>
    </div>
  );
}
