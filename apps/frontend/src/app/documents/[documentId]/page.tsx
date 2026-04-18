import { DocumentDetail } from "@/components/documents/document-detail";

export default async function DocumentDetailPage({
  params,
}: {
  params: Promise<{ documentId: string }>;
}) {
  const { documentId } = await params;
  return (
    <div className="mx-auto max-w-5xl p-6">
      <DocumentDetail documentId={documentId} />
    </div>
  );
}
