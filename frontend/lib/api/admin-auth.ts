import { requestJson } from "@/lib/api/client";
import type { AdminMe, AuthTokenResponse } from "@/types/api";

export function loginAdmin(payload: { username: string; password: string }) {
  return requestJson<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: payload,
    token: ""
  });
}

export function getCurrentAdmin(token?: string) {
  return requestJson<AdminMe>("/auth/me", {
    token
  });
}
