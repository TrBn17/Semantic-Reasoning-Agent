import { DocumentTable } from "@/components/documents/document-table";
import { UploadDialog } from "@/components/documents/upload-dialog";

export default function DocumentsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Documents</h1>
          <p className="text-sm text-muted-foreground">
            Upload files for ingestion. Indexed chunks become available for
            retrieval and ontology extraction.
          </p>
        </div>
        <UploadDialog />
      </div>
      <DocumentTable />
    </div>
  );
}
