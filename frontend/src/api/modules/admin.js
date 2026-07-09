import { api } from "../client.js";

export function getAuthRequests() {
  return api("/api/admin/auth-requests");
}

export function getFeedback() {
  return api("/api/admin/feedback");
}

export function getUsers() {
  return api("/api/admin/users");
}

export function getStats() {
  return api("/api/admin/stats");
}

export function auditUser(userNo, authStatus) {
  return api(`/api/admin/users/${userNo}/auth`, { method: "POST", body: JSON.stringify({ authStatus }) });
}

export function replyFeedback(feedbackNo, reply) {
  return api(`/api/admin/feedback/${feedbackNo}/reply`, { method: "POST", body: JSON.stringify({ reply }) });
}

export function setUserStatus(userNo, status) {
  return api(`/api/admin/users/${userNo}/status`, { method: "POST", body: JSON.stringify({ status }) });
}
