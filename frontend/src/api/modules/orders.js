import { api } from "../client.js";

export function getMyOrders() {
  return api("/api/orders/mine");
}

export function orderAction(orderNo, action) {
  return api(`/api/orders/${orderNo}/action`, { method: "POST", body: JSON.stringify({ action }) });
}

export function createReview(orderNo, body) {
  return api(`/api/orders/${orderNo}/reviews`, { method: "POST", body: JSON.stringify(body) });
}
