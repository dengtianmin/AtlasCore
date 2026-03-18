export const ADMIN_TOKEN_COOKIE = "atlascore_admin_token";
export const USER_TOKEN_COOKIE = "atlascore_user_token";

function readCookieValue(name: string) {
  if (typeof document === "undefined") {
    return "";
  }

  const tokenCookie = document.cookie.split("; ").find((entry) => entry.startsWith(`${name}=`));
  return tokenCookie ? decodeURIComponent(tokenCookie.split("=")[1]) : "";
}

function writeCookieValue(name: string, token: string) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
}

function clearCookieValue(name: string) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getAdminToken() {
  return readCookieValue(ADMIN_TOKEN_COOKIE);
}

export function setAdminToken(token: string) {
  writeCookieValue(ADMIN_TOKEN_COOKIE, token);
}

export function clearAdminToken() {
  clearCookieValue(ADMIN_TOKEN_COOKIE);
}

export function getUserToken() {
  return readCookieValue(USER_TOKEN_COOKIE);
}

export function setUserToken(token: string) {
  writeCookieValue(USER_TOKEN_COOKIE, token);
}

export function clearUserToken() {
  clearCookieValue(USER_TOKEN_COOKIE);
}
