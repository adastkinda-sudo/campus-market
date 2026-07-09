import { api } from "../client.js";

export function getNotifications() {
  return api("/api/notifications");
}

export function readAll() {
  return api("/api/notifications/read-all", { method: "POST", body: "{}" });
}

export function readOne(no) {
  return api(`/api/notifications/${no}/read`, { method: "POST", body: "{}" });
}
