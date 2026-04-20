"use client";

import { DocumentTable } from "@/components/documents/document-table";
import { UploadDialog } from "@/components/documents/upload-dialog";
import { useI18n } from "@/src/shared/i18n/use-language";

export default function DocumentsPage() {
  const { t } = useI18n();
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{t.documentsPage.title}</h1>
          <p className="text-sm text-muted-foreground">
            {t.documentsPage.description}
          </p>
        </div>
        <UploadDialog />
      </div>
      <DocumentTable />
    </div>
  );
}
