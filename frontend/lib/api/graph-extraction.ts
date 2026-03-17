import { requestJson } from "@/lib/api/client";
import type {
  ExtractionTask,
  ExtractionTaskListResponse,
  GraphManagedFile,
  GraphManagedFileListResponse,
  GraphModelSetting,
  GraphPromptSetting,
  GraphFileOperation
} from "@/types/api";

export function listSqliteFiles(limit = 50, offset = 0) {
  return requestJson<GraphManagedFileListResponse>(`/api/admin/graph/sqlite-files?limit=${limit}&offset=${offset}`);
}

export function uploadSqliteFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<GraphManagedFile>("/api/admin/graph/sqlite-files/upload", {
    method: "POST",
    body: formData
  });
}

export function activateSqliteFile(documentId: string) {
  return requestJson<GraphFileOperation>(`/api/admin/graph/sqlite-files/${documentId}/activate`, {
    method: "POST"
  });
}

export function listMdFiles(limit = 50, offset = 0) {
  return requestJson<GraphManagedFileListResponse>(`/api/admin/graph/md-files?limit=${limit}&offset=${offset}`);
}

export function uploadMdFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<GraphManagedFile>("/api/admin/graph/md-files/upload", {
    method: "POST",
    body: formData
  });
}

export function deleteMdFile(documentId: string) {
  return requestJson<void>(`/api/admin/graph/md-files/${documentId}`, {
    method: "DELETE"
  });
}

export function createExtractionTask(documentIds: string[]) {
  return requestJson<ExtractionTask>("/api/admin/graph/extraction-tasks", {
    method: "POST",
    body: { document_ids: documentIds }
  });
}

export function listExtractionTasks(limit = 20, offset = 0) {
  return requestJson<ExtractionTaskListResponse>(`/api/admin/graph/extraction-tasks?limit=${limit}&offset=${offset}`);
}

export function getExtractionTask(taskId: string) {
  return requestJson<ExtractionTask>(`/api/admin/graph/extraction-tasks/${taskId}`);
}

export function getPromptSetting() {
  return requestJson<GraphPromptSetting>("/api/admin/graph/prompt-settings");
}

export function updatePromptSetting(promptText: string) {
  return requestJson<GraphPromptSetting>("/api/admin/graph/prompt-settings", {
    method: "PUT",
    body: { prompt_text: promptText }
  });
}

export function getModelSetting() {
  return requestJson<GraphModelSetting>("/api/admin/graph/model-settings");
}

export function updateModelSetting(payload: {
  provider: string;
  model_name: string;
  api_base_url?: string | null;
  api_key?: string | null;
  enabled: boolean;
}) {
  return requestJson<GraphModelSetting>("/api/admin/graph/model-settings", {
    method: "PUT",
    body: payload
  });
}
