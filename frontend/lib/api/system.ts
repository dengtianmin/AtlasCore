import { requestJson } from "@/lib/api/client";
import type { HealthStatus, RootInfo } from "@/types/api";

export function getHealth() {
  return requestJson<HealthStatus>("/health");
}

export function getRootInfo() {
  return requestJson<RootInfo>("/");
}
