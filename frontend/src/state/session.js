import { reactive } from "vue";
import { api } from "../api/client.js";

export const state = reactive({
  token: localStorage.getItem("campus-market-token") || "",
  principal: null,
  categories: [],
  locations: [],
  announcements: [],
  dashboard: null,
  unreadCount: 0,
  notice: "",
  noticeError: false,
  theme: localStorage.getItem("campus-market-theme") || "light",
});

export function isUser() {
  return state.principal?.kind === "user";
}

export function isAdmin() {
  return state.principal?.kind === "admin";
}

export function canTrade() {
  return isUser() && state.principal.authStatus === "已认证" && state.principal.status === "正常" && state.principal.creditScore >= 60;
}

export function notify(message, isError = false) {
  state.notice = message;
  state.noticeError = isError;
  if (message) {
    window.setTimeout(() => {
      if (state.notice === message) state.notice = "";
    }, 2600);
  }
}

export async function loadMe() {
  if (!state.token) {
    state.principal = null;
    return;
  }
  try {
    const data = await api("/api/me");
    state.principal = data.principal;
    if (!data.principal) {
      state.token = "";
      localStorage.removeItem("campus-market-token");
    }
  } catch {
    state.token = "";
    state.principal = null;
    localStorage.removeItem("campus-market-token");
  }
}

export async function loadCommon() {
  const [categories, locations, announcements, dashboard] = await Promise.all([
    api("/api/categories"),
    api("/api/locations"),
    api("/api/announcements"),
    api("/api/dashboard"),
  ]);
  state.categories = categories.categories || [];
  state.locations = locations.locations || [];
  state.announcements = announcements.announcements || [];
  state.dashboard = dashboard;
  if (isUser()) {
    try {
      const notifications = await api("/api/notifications");
      state.unreadCount = notifications.unreadCount || 0;
    } catch {
      state.unreadCount = 0;
    }
  } else {
    state.unreadCount = 0;
  }
}

export async function login(account, password) {
  const data = await api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ account, password }),
  });
  state.token = data.token;
  state.principal = data.principal;
  localStorage.setItem("campus-market-token", state.token);
  await loadCommon();
  notify("登录成功");
}

export async function logout() {
  await api("/api/auth/logout", { method: "POST", body: "{}" }).catch(() => {});
  state.token = "";
  state.principal = null;
  localStorage.removeItem("campus-market-token");
  await loadCommon();
  notify("已退出登录");
}

export function setTheme(theme) {
  state.theme = theme;
  localStorage.setItem("campus-market-theme", theme);
  document.documentElement.dataset.theme = theme;
}
