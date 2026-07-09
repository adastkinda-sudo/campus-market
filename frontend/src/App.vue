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
      <button class="icon-btn theme-toggle" type="button" title="切换深色模式" @click="toggleTheme">{{ session.theme === "dark" ? "☀️" : "🌙" }}</button>
      <nav>
        <RouterLink v-for="item in navItems" :key="item.to" class="nav-btn" :to="item.to">
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>

  <main class="shell">
    <GlobalSearch v-if="showGlobalSearch" />
    <section v-if="session.notice" :class="['notice', session.noticeError ? 'error' : '']">{{ session.notice }}</section>
    <RouterView />
  </main>

  <SideFloat />
</template>

<script setup>
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";
import GlobalSearch from "./components/GlobalSearch.vue";
import SideFloat from "./components/SideFloat.vue";
import { useCommonStore } from "./stores/common.js";
import { useSessionStore } from "./stores/session.js";

const route = useRoute();
const session = useSessionStore();
const common = useCommonStore();

const showGlobalSearch = computed(() => route.path !== "/account");

const userBadge = computed(() => {
  if (!session.principal) return "游客浏览";
  if (session.isAdmin) return `管理员 ${session.principal.username}`;
  return `${session.principal.nickname} · ${session.principal.userType || "学生"} · ${session.principal.authStatus} · 信用 ${session.principal.creditScore}`;
});

const navItems = computed(() => {
  const items = [
    { to: "/", label: "项目介绍" },
    { to: "/items", label: "浏览物品" },
    { to: "/wanted", label: "求购市场" },
    { to: "/users", label: "用户搜索" },
    { to: "/contact", label: "联系我们" },
  ];
  if (session.isUser) {
    items.push(
      { to: "/favorites", label: "我的收藏" },
      { to: "/notifications", label: session.unreadCount ? `通知(${session.unreadCount})` : "通知" },
      { to: "/publish", label: "发布管理" },
      { to: "/orders", label: "我的订单" },
      { to: "/chats", label: "私信" },
    );
  }
  if (session.isAdmin) items.push({ to: "/admin", label: "后台管理" });
  items.push({ to: "/account", label: session.principal ? "账号" : "登录" });
  return items;
});

function toggleTheme() {
  session.setTheme(session.theme === "dark" ? "light" : "dark");
}

onMounted(async () => {
  session.setTheme(session.theme);
  await session.loadMe();
  await common.loadCommon();
});
</script>
