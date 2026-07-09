import { api } from "../client.js";

export function searchUsers(keyword) {
  return api(`/api/users?keyword=${encodeURIComponent(keyword)}`);
}

export function getUserProfile(id) {
  return api(`/api/users/${id}`);
}
