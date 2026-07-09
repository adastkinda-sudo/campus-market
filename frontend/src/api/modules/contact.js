import { api } from "../client.js";

export function getMyFeedback() {
  return api("/api/contact/mine");
}

export function submitFeedback(body) {
  return api("/api/contact", { method: "POST", body: JSON.stringify(body) });
}
