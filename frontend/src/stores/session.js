import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { getMe, login as apiLogin, logout as apiLogout } from "../api/modules/auth.js";

const TOKEN_KEY = "campus-market-token";
const PRINCIPAL_KEY = "campus-market-principal";

export const useSessionStore = defineStore("session", () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || "");
  const principal = ref(JSON.parse(localStorage.getItem(PRINCIPAL_KEY) || "null"));
  const theme = ref(localStorage.getItem("campus-market-theme") || "light");
  const unreadCount = ref(0);
  const notice = ref("");
  const noticeError = ref(false);

  const isUser = computed(() => principal.value?.kind === "user");
  const isAdmin = computed(() => principal.value?.kind === "admin");
  const canTrade = computed(
    () =>
      isUser.value &&
      principal.value?.authStatus === "已认证" &&
      principal.value?.status === "正常" &&
      principal.value?.creditScore >= 60,
  );

  function _persist() {
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value);
    else localStorage.removeItem(TOKEN_KEY);
    if (principal.value) localStorage.setItem(PRINCIPAL_KEY, JSON.stringify(principal.value));
    else localStorage.removeItem(PRINCIPAL_KEY);
  }

  function notify(message, isError = false) {
    notice.value = message;
    noticeError.value = isError;
    if (message) {
      window.setTimeout(() => {
        if (notice.value === message) {
          notice.value = "";
        }
      }, 2600);
    }
  }

  async function loadMe() {
    if (!token.value) {
      principal.value = null;
      _persist();
      return;
    }
    try {
      const data = await getMe();
      principal.value = data.principal;
      if (!data.principal) {
        token.value = "";
      }
    } catch {
      token.value = "";
      principal.value = null;
    }
    _persist();
  }

  async function login(account, password) {
    const data = await apiLogin(account, password);
    token.value = data.token;
    principal.value = data.principal;
    _persist();
    notify("登录成功");
  }

  async function logout() {
    await apiLogout();
    token.value = "";
    principal.value = null;
    _persist();
    notify("已退出登录");
  }

  function setTheme(value) {
    theme.value = value;
    localStorage.setItem("campus-market-theme", value);
    document.documentElement.dataset.theme = value;
  }

  return {
    token,
    principal,
    theme,
    unreadCount,
    notice,
    noticeError,
    isUser,
    isAdmin,
    canTrade,
    notify,
    loadMe,
    login,
    logout,
    setTheme,
  };
});
