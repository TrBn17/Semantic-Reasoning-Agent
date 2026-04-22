import { apiFetch } from "@/shared/api/client";
import type {
  DocumentBatchUploadResponse,
  DocumentIngestionCapabilitiesResponse,
  DocumentJobResponse,
  DocumentReprocessResponse,
  DocumentResponse,
  DocumentUploadFailure,
} from "@/shared/api/types";

export function listDocuments(): Promise<DocumentResponse[]> {
  return apiFetch<DocumentResponse[]>("/documents", { method: "GET" });
}

export function getDocumentIngestionCapabilities(): Promise<DocumentIngestionCapabilitiesResponse> {
  return apiFetch<DocumentIngestionCapabilitiesResponse>("/documents/options", {
    method: "GET",
  });
}

export function getDocument(id: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/documents/${id}`, { method: "GET" });
}

export function listDocumentJobs(id: string): Promise<DocumentJobResponse[]> {
  return apiFetch<DocumentJobResponse[]>(`/documents/${id}/jobs`, { method: "GET" });
}

export function reprocessDocument(id: string): Promise<DocumentReprocessResponse> {
  return apiFetch<DocumentReprocessResponse>(`/documents/${id}/reprocess`, {
    method: "POST",
  });
}

export interface UploadDocumentInput {
  file: File;
  title?: string;
  workspaceId?: string;
  tags?: string[];
  pdfMode?: "fast" | "accurate";
  outputFormat?: "markdown" | "html" | "json" | "chunks";
  extractImages?: boolean;
}

export function uploadDocument(input: UploadDocumentInput): Promise<DocumentResponse> {
  const form = new FormData();
  form.append("file", input.file);
  if (input.title) form.append("title", input.title);
  if (input.workspaceId) form.append("workspace_id", input.workspaceId);
  if (input.tags && input.tags.length > 0) {
    form.append("tags", input.tags.join(","));
  }
  if (input.pdfMode) form.append("pdf_mode", input.pdfMode);
  if (input.outputFormat) form.append("output_format", input.outputFormat);
  if (typeof input.extractImages === "boolean") {
    form.append("extract_images", String(input.extractImages));
  }
  return apiFetch<DocumentResponse>("/documents/upload", {
    method: "POST",
    body: form,
  });
}

export interface UploadDocumentsInput {
  files: File[];
  workspaceId?: string;
  tags?: string[];
  pdfMode?: "fast" | "accurate";
  outputFormat?: "markdown" | "html" | "json" | "chunks";
  extractImages?: boolean;
}

export function uploadDocuments(input: UploadDocumentsInput): Promise<DocumentBatchUploadResponse> {
  return Promise.allSettled(
    input.files.map((file) =>
      uploadDocument({
        file,
        workspaceId: input.workspaceId,
        tags: input.tags,
        pdfMode: input.pdfMode,
        outputFormat: input.outputFormat,
        extractImages: input.extractImages,
      }),
    ),
  ).then((results) => {
    const uploaded: DocumentResponse[] = [];
    const failed: DocumentUploadFailure[] = [];

    results.forEach((result, index) => {
      const file = input.files[index];
      if (result.status === "fulfilled") {
        uploaded.push(result.value);
        return;
      }

      failed.push({
        filename: file?.name ?? "unknown",
        reason: result.reason instanceof Error ? result.reason.message : "Upload failed",
      });
    });

    return { uploaded, failed };
  });
}
