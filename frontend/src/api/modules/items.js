import { api } from "../client.js";

export function searchItems(params = {}) {
  const query = new URLSearchParams(params).toString();
  return api(`/api/items?${query}`);
}

export function getItem(itemNo) {
  return api(`/api/items/${itemNo}`);
}

export function createItem(body) {
  return api("/api/items", { method: "POST", body: JSON.stringify(body) });
}

export function updateItem(itemNo, body) {
  return api(`/api/items/${itemNo}`, { method: "PUT", body: JSON.stringify(body) });
}

export function updateItemStatus(itemNo, status) {
  return api(`/api/items/${itemNo}/status`, { method: "POST", body: JSON.stringify({ status }) });
}

export function deleteItem(itemNo) {
  return api(`/api/items/${itemNo}`, { method: "DELETE" });
}

export function toggleFavorite(itemNo, isFavorite) {
  const method = isFavorite ? "DELETE" : "POST";
  return api(`/api/items/${itemNo}/favorite`, { method });
}

export function createOrder(itemNo, body) {
  return api(`/api/items/${itemNo}/orders`, { method: "POST", body: JSON.stringify(body) });
}

export function createMessage(itemNo, content) {
  return api(`/api/items/${itemNo}/messages`, { method: "POST", body: JSON.stringify({ content }) });
}
