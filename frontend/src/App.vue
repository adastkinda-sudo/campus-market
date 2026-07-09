<template>
  <header class="topbar">
    <RouterLink class="brand" to="/">
      <span class="brand-mark">C2C</span>
      <div>
        <strong>华东理工大学校园二手交易系统</strong>
        <span>{{ userBadge }}</span>
      </div>
    </RouterLink>
    <div class="topbar-actions">
      <button class="icon-btn theme-toggle" type="button" title="切换深色模式" @click="toggleTheme">{{ state.theme === "dark" ? "☀️" : "🌙" }}</button>
      <nav>
        <RouterLink v-for="item in navItems" :key="item.to" class="nav-btn" :to="item.to">
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>

  <main class="shell">
    <GlobalSearch v-if="showGlobalSearch" />
    <section v-if="state.notice" :class="['notice', state.noticeError ? 'error' : '']">{{ state.notice }}</section>
    <RouterView />
  </main>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import GlobalSearch from "./components/GlobalSearch.vue";
import { isAdmin, isUser, loadCommon, loadMe, setTheme, state } from "./state/session.js";

const route = useRoute();
const showGlobalSearch = computed(() => route.path !== "/account");

const userBadge = computed(() => {
  if (!state.principal) return "游客浏览";
  if (isAdmin()) return `管理员 ${state.principal.username}`;
  return `${state.principal.nickname} · ${state.principal.userType || "学生"} · ${state.principal.authStatus} · 信用 ${state.principal.creditScore}`;
});

const navItems = computed(() => {
  const items = [
    { to: "/", label: "项目介绍" },
    { to: "/items", label: "浏览物品" },
    { to: "/wanted", label: "求购市场" },
    { to: "/users", label: "用户搜索" },
    { to: "/contact", label: "联系我们" },
  ];
  if (isUser()) {
    items.push(
      { to: "/favorites", label: "我的收藏" },
      { to: "/notifications", label: state.unreadCount ? `通知(${state.unreadCount})` : "通知" },
      { to: "/publish", label: "发布管理" },
      { to: "/orders", label: "我的订单" },
      { to: "/chats", label: "私信" },
    );
  }
  if (isAdmin()) items.push({ to: "/admin", label: "后台管理" });
  items.push({ to: "/account", label: state.principal ? "账号" : "登录" });
  return items;
});

function toggleTheme() {
  setTheme(state.theme === "dark" ? "light" : "dark");
}

onMounted(async () => {
  setTheme(state.theme);
  await loadMe();
  await loadCommon();
});
</script>
