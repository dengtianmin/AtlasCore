import { requestBlob, requestJson } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/utils";
import type { GraphAdminStatus, GraphFileOperation, GraphReload } from "@/types/api";

export function getGraphAdminStatus() {
  return requestJson<GraphAdminStatus>("/api/admin/graph/status");
}

export function reloadGraph() {
  return requestJson<GraphReload>("/api/admin/graph/reload", {
    method: "POST"
  });
}

export function exportGraph() {
  return requestJson<GraphFileOperation>("/api/admin/graph/export", {
    method: "POST"
  });
}

export function importGraph(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<GraphFileOperation>("/api/admin/graph/import", {
    method: "POST",
    body: formData
  });
}

export async function downloadGraphExport(filename: string) {
  const blob = await requestBlob(`/api/admin/graph/download/${filename}`);
  triggerBrowserDownload(blob, filename);
}
