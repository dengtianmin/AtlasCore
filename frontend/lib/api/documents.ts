import { requestJson } from "@/lib/api/client";
import type { DocumentListResponse, DocumentRecord, SyncResponse } from "@/types/api";

export function listDocuments(limit = 50, offset = 0) {
  return requestJson<DocumentListResponse>(`/admin/documents?limit=${limit}&offset=${offset}`);
}

export function getDocument(documentId: string) {
  return requestJson<DocumentRecord>(`/admin/documents/${documentId}`);
}

export function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<DocumentRecord>("/admin/documents/upload", {
    method: "POST",
    body: formData
  });
}

export function deleteDocument(documentId: string) {
  return requestJson<void>(`/admin/documents/${documentId}`, {
    method: "DELETE"
  });
}

export function syncDocumentToGraph(documentId: string) {
  return requestJson<SyncResponse>(`/admin/documents/${documentId}/graph-sync`, {
    method: "POST"
  });
}

export function syncDocumentToDify(documentId: string) {
  return requestJson<SyncResponse>(`/admin/documents/${documentId}/dify-sync`, {
    method: "POST"
  });
}
