import { requestJson } from "@/lib/api/client";
import type { AdminLogListResponse, AdminLogRecord } from "@/types/api";

type LogQuery = {
  keyword?: string;
  source?: string;
  liked?: string;
  rating?: string;
  dateFrom?: string;
  dateTo?: string;
};

export function listAdminLogs(query: LogQuery = {}) {
  const params = new URLSearchParams();
  params.set("limit", "100");
  if (query.keyword) params.set("keyword", query.keyword);
  if (query.source) params.set("source", query.source);
  if (query.liked) params.set("liked", query.liked);
  if (query.rating) params.set("rating", query.rating);
  if (query.dateFrom) params.set("date_from", query.dateFrom);
  if (query.dateTo) params.set("date_to", query.dateTo);

  return requestJson<AdminLogListResponse>(`/api/admin/logs?${params.toString()}`);
}

export function getAdminLog(recordId: string) {
  return requestJson<AdminLogRecord>(`/api/admin/logs/${recordId}`);
}
