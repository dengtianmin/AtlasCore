import { requestBlob, requestJson } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/utils";
import type { ExportListResponse, ExportRecord } from "@/types/api";

export function listExports() {
  return requestJson<ExportListResponse>("/api/admin/exports");
}

export function getLatestExport() {
  return requestJson<ExportRecord>("/api/admin/exports/latest");
}

export function triggerLogExport(operator: string) {
  return requestJson<ExportRecord>("/api/admin/exports/qa-logs", {
    method: "POST",
    body: { operator }
  });
}

export async function downloadExport(filename: string) {
  const blob = await requestBlob(`/api/admin/exports/download/${filename}`);
  triggerBrowserDownload(blob, filename);
}
