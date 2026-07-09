import { api } from "../client.js";

export function getWanted() {
  return api("/api/wanted");
}

export function createWanted(body) {
  return api("/api/wanted", { method: "POST", body: JSON.stringify(body) });
}
