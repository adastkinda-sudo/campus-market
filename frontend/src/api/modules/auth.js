import { api } from "../client.js";

export function login(account, password) {
  return api("/api/auth/login", { method: "POST", body: JSON.stringify({ account, password }) });
}

export function logout() {
  return api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
}

export function register(body) {
  return api("/api/auth/register", { method: "POST", body: JSON.stringify(body) });
}

export function getMe() {
  return api("/api/me");
}

export function updateProfile(profile) {
  return api("/api/me", { method: "PUT", body: JSON.stringify(profile) });
}

export function submitAuth(body) {
  return api("/api/auth/submit-auth", { method: "POST", body: JSON.stringify(body) });
}
