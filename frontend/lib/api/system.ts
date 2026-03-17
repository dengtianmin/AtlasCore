import { requestJson } from "@/lib/api/client";
import type { DifyDebugLogListResponse, DifyDebugRequest, DifyDebugResponse, HealthStatus, RootInfo } from "@/types/api";

export function getHealth() {
  return requestJson<HealthStatus>("/health");
}

export function getReadiness() {
  return requestJson<HealthStatus>("/health/ready");
}

export function getRootInfo() {
  return requestJson<RootInfo>("/");
}

export function getAdminSystemStatus() {
  return requestJson<HealthStatus>("/api/admin/system/status");
}

export function runDifyDebug(payload: DifyDebugRequest) {
  return requestJson<DifyDebugResponse>("/api/admin/system/dify/debug", {
    method: "POST",
    body: payload
  });
}

export function listDifyDebugLogs(limit = 20) {
  return requestJson<DifyDebugLogListResponse>(`/api/admin/system/dify/debug/logs?limit=${limit}`);
}
