<template>
  <template v-if="!isAuthPage">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <img class="brand-logo" src="/assets/liwu-logo.svg" alt="理物" />
        <div class="brand-copy">
          <strong>华理校内二手交易平台</strong>
          <span>让闲置在校园里流动</span>
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

  <RouterView v-else />
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import SideFloat from "./components/SideFloat.vue";
import { useCommonStore } from "./stores/common.js";
import { useSessionStore } from "./stores/session.js";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const common = useCommonStore();

const searchType = ref("item");
const searchKeyword = ref("");

const isAuthPage = computed(() => route.path === "/account" && !session.principal);

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
  await session.loadMe();
  await common.loadCommon();
});
</script>

<style scoped>
/* ===== Topbar ===== */
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(20px) saturate(1.6);
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: auto; flex-shrink: 0;
  color: var(--ink);
  text-decoration: none;
}
.brand-logo { display: block; width: 92px; height: auto; flex: 0 0 auto; }
.brand-copy { display: grid; gap: 2px; }
.brand strong { display: block; font-size: 16px; line-height: 1.25; font-weight: 800; letter-spacing: -0.01em; }
.brand span:last-child { display: block; margin-top: 2px; color: var(--muted); font-size: 12px; font-weight: 600; }

/* ===== Navigation ===== */
#nav, .topbar-actions nav {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  padding: 6px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.72);
}
.nav-btn {
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  min-height: 34px;
  padding: 7px 14px;
  color: var(--ink-soft);
  border-radius: 999px;
  font-weight: 650;
  text-decoration: none;
  background: transparent;
  transition: transform 0.16s ease, background 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, color 0.16s ease;
}
.nav-btn:hover {
  transform: translateY(-1px);
  background: #fff;
  border-color: rgba(226, 232, 240, 0.9);
  box-shadow: var(--shadow-sm);
}
.nav-btn.active, .nav-btn.router-link-active {
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  box-shadow: 0 8px 18px rgba(13, 148, 136, 0.24);
}

/* ===== Topbar Actions ===== */
.topbar-actions { display: flex; align-items: center; gap: 10px; }

/* ===== Topbar Search ===== */
.topbar-search {
  flex: 1;
  max-width: 520px;
  display: flex;
  align-items: center;
  border: 2px solid var(--primary);
  border-radius: 999px;
  background: var(--surface);
  overflow: hidden;
}
.search-type { display: flex; align-items: center; padding: 2px; padding-left: 6px; padding-right: 12px; gap: 2px; flex-shrink: 0; position: relative; }
.search-type::after {
  content: "";
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 1px;
  height: 22px;
  border-radius: 999px;
  background: var(--line-strong);
}
.type-btn {
  min-height: 30px;
  padding: 5px 12px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
}
.type-btn:hover { color: var(--primary); background: rgba(13, 148, 136, 0.06); }
.type-btn.active { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25); }
.topbar-search input {
  flex: 1;
  min-height: 42px;
  padding: 8px 8px 8px 4px;
  border: none;
  background: transparent;
  color: var(--ink);
  font-size: 14px;
  outline: none;
  box-shadow: none;
}
.topbar-search input::placeholder { color: var(--muted); opacity: 0.7; }
.search-submit {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin: 2px;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}
.search-submit:hover { transform: scale(1.05); box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35); }

/* ===== Mine Button ===== */
.mine-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px 6px 6px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--ink);
  text-decoration: none;
  font-size: 13px;
  font-weight: 650;
  transition: all 0.16s ease;
}
.mine-btn:hover { border-color: var(--primary); box-shadow: var(--shadow-sm); }
.mine-avatar { width: 30px; height: 30px; border-radius: 999px; object-fit: cover; }
.mine-avatar-placeholder {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--primary-dark), var(--primary-light));
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}
.mine-label { font-size: 13px; font-weight: 650; }

/* ===== Responsive ===== */
@media (max-width: 980px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  #nav { justify-content: flex-start; width: 100%; }
}
@media (max-width: 720px) {
  .topbar-search { max-width: none; order: 3; width: 100%; }
  .topbar { flex-wrap: wrap; }
  .brand { flex-shrink: 0; }
}
@media (max-width: 620px) {
  .topbar { padding: 12px 14px; }
  .brand { min-width: 0; }
  .brand-logo { width: 78px; }
  .brand-copy strong { font-size: 14px; }
  .brand .brand-copy span { display: none; }
  #nav, .topbar-actions nav { overflow-x: auto; flex-wrap: nowrap; justify-content: flex-start; }
  .topbar-actions { min-width: 0; }
  .nav-btn { white-space: nowrap; }
}
</style>
