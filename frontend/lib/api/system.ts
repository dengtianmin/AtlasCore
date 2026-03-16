import { requestJson } from "@/lib/api/client";
import type { HealthStatus, RootInfo } from "@/types/api";

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
