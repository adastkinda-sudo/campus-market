import { api } from "../client.js";

export function getConversations() {
  return api("/api/chats");
}

export function getMessages(conversationNo) {
  return api(`/api/chats/${conversationNo}/messages`);
}

export function sendMessage(conversationNo, content) {
  return api(`/api/chats/${conversationNo}/messages`, { method: "POST", body: JSON.stringify({ content }) });
}

export function createChat(body) {
  return api("/api/chats", { method: "POST", body: JSON.stringify(body) });
}
