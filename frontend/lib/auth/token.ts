export const ADMIN_TOKEN_COOKIE = "atlascore_admin_token";

export function getAdminToken() {
  if (typeof document === "undefined") {
    return "";
  }

  const tokenCookie = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${ADMIN_TOKEN_COOKIE}=`));

  return tokenCookie ? decodeURIComponent(tokenCookie.split("=")[1]) : "";
}

export function setAdminToken(token: string) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${ADMIN_TOKEN_COOKIE}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
}

export function clearAdminToken() {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${ADMIN_TOKEN_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}
