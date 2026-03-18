import { requestJson } from "@/lib/api/client";
import type { AuthTokenResponse, UserMe } from "@/types/api";

export function registerUser(payload: { student_id: string; name: string; password: string }) {
  return requestJson<UserMe>("/users/register", {
    method: "POST",
    auth: "none",
    body: payload
  });
}

export function loginUser(payload: { student_id: string; password: string }) {
  return requestJson<AuthTokenResponse>("/users/login", {
    method: "POST",
    auth: "none",
    body: payload
  });
}

export function getCurrentUser(token?: string) {
  return requestJson<UserMe>("/users/me", {
    auth: "user",
    token
  });
}
