<template>
  <header class="topbar">
    <RouterLink class="brand" to="/">
      <span class="brand-mark">C2C</span>
      <div>
        <strong>华东理工大学校园二手交易系统</strong>
      </div>
    </RouterLink>

    <form class="topbar-search" @submit.prevent="doSearch">
      <div class="search-type">
        <button :class="['type-btn', searchType === 'item' ? 'active' : '']" type="button" @click="searchType = 'item'">商品</button>
        <button :class="['type-btn', searchType === 'user' ? 'active' : '']" type="button" @click="searchType = 'user'">用户</button>
      </div>
      <input
        v-model="searchKeyword"
        type="search"
        :placeholder="searchType === 'item' ? '搜索商品名称、描述...' : '搜索用户昵称、姓名、学号...'"
        autocomplete="off"
      />
      <button class="search-submit" type="submit">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
      </button>
    </form>

    <div class="topbar-actions">
      <button class="icon-btn theme-toggle" type="button" title="切换深色模式" @click="toggleTheme">{{ session.theme === "dark" ? "☀️" : "🌙" }}</button>
      <RouterLink class="mine-btn" to="/account">
        <img v-if="session.principal?.avatarUrl" class="mine-avatar" :src="session.principal.avatarUrl" alt="" />
        <span v-else class="mine-avatar-placeholder">{{ session.principal ? session.principal.nickname?.[0] : "我" }}</span>
        <span class="mine-label">{{ session.principal ? "我的" : "登录" }}</span>
      </RouterLink>
    </div>
  </header>

  <main class="shell">
    <section v-if="session.notice" :class="['notice', session.noticeError ? 'error' : '']">{{ session.notice }}</section>
    <RouterView />
  </main>

  <SideFloat />
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";
import SideFloat from "./components/SideFloat.vue";
import { useCommonStore } from "./stores/common.js";
import { useSessionStore } from "./stores/session.js";

const router = useRouter();
const session = useSessionStore();
const common = useCommonStore();

const searchType = ref("item");
const searchKeyword = ref("");

function toggleTheme() {
  session.setTheme(session.theme === "dark" ? "light" : "dark");
}

async function doSearch() {
  const kw = searchKeyword.value.trim();
  if (!kw) return;
  if (searchType.value === "item") {
    await router.push({ path: "/items", query: { keyword: kw } });
  } else {
    await router.push({ path: "/users", query: { keyword: kw } });
  }
}

onMounted(async () => {
  session.setTheme(session.theme);
  await session.loadMe();
  await common.loadCommon();
});
</script>
