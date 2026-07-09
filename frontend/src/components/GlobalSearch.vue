<template>
  <section ref="root" class="global-search-shell" @focusout="handleFocusOut">
    <form class="global-search" @submit.prevent="submitSearch">
      <span class="global-search-icon">⌕</span>
      <input
        v-model="keyword"
        type="search"
        placeholder="搜索商品、卖家、用户昵称或学号"
        autocomplete="off"
        @focus="handleFocus"
        @keydown.esc="closePanel"
      />
      <button class="btn" type="submit">搜索</button>
    </form>

    <div v-if="panelVisible" class="global-search-panel">
      <div v-if="loading" class="search-loading">搜索中...</div>
      <template v-else>
        <div class="search-result-group">
          <div class="search-panel-head">
            <strong>商品</strong>
            <RouterLink class="text-link" :to="itemsRoute" @click="closePanel">查看全部</RouterLink>
          </div>
          <button
            v-for="item in items"
            :key="item.itemNo"
            class="search-result-row"
            type="button"
            @mousedown.prevent="openItem(item)"
          >
            <img :src="defaultImage(item)" alt="" />
            <span>
              <strong>{{ item.title }}</strong>
              <small>{{ item.categoryName }} · {{ item.campusName || "校区未标注" }}</small>
            </span>
            <em>{{ money(item.sellPrice) }}</em>
          </button>
          <p v-if="!items.length" class="search-empty">没有找到相关商品</p>
        </div>

        <div class="search-result-group">
          <div class="search-panel-head">
            <strong>用户</strong>
            <RouterLink class="text-link" :to="usersRoute" @click="closePanel">进入用户搜索</RouterLink>
          </div>
          <RouterLink
            v-for="user in users"
            :key="user.userNo"
            class="search-result-row user-result"
            :to="`/users/${user.userNo}`"
            @click="closePanel"
          >
            <img :src="user.avatarUrl || '/assets/default-avatar.svg'" alt="" />
            <span>
              <strong>{{ user.nickname }}</strong>
              <small>{{ user.userType }} · {{ user.authStatus }} · 信用 {{ user.creditScore }}</small>
            </span>
          </RouterLink>
          <p v-if="!users.length" class="search-empty">没有找到相关用户</p>
        </div>
      </template>
    </div>
  </section>

  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" />
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { searchItems } from "../api/modules/items.js";
import { searchUsers } from "../api/modules/users.js";
import { useSessionStore } from "../stores/session.js";
import { defaultImage, money } from "../utils.js";
import ItemDetailModal from "./ItemDetailModal.vue";

const router = useRouter();
const session = useSessionStore();

const root = ref(null);
const keyword = ref("");
const items = ref([]);
const users = ref([]);
const loading = ref(false);
const open = ref(false);
const detailOpen = ref(false);
const activeItemNo = ref(null);
let debounceTimer = 0;
let requestId = 0;

const trimmedKeyword = computed(() => keyword.value.trim());
const panelVisible = computed(() => open.value && trimmedKeyword.value);
const itemsRoute = computed(() => ({ path: "/items", query: { keyword: trimmedKeyword.value } }));
const usersRoute = computed(() => ({ path: "/users", query: { keyword: trimmedKeyword.value } }));

watch(keyword, () => {
  window.clearTimeout(debounceTimer);
  if (!trimmedKeyword.value) {
    items.value = [];
    users.value = [];
    loading.value = false;
    return;
  }
  debounceTimer = window.setTimeout(search, 220);
});

onBeforeUnmount(() => {
  window.clearTimeout(debounceTimer);
});

function handleFocus() {
  open.value = true;
  if (trimmedKeyword.value && !items.value.length && !users.value.length) search();
}

function handleFocusOut() {
  window.setTimeout(() => {
    if (root.value && !root.value.contains(document.activeElement)) closePanel();
  }, 80);
}

function closePanel() {
  open.value = false;
}

async function search() {
  const keywordValue = trimmedKeyword.value;
  if (!keywordValue) return;
  const currentRequest = ++requestId;
  loading.value = true;
  try {
    const [itemData, userData] = await Promise.all([
      searchItems({ keyword: keywordValue, sort: "hot" }),
      searchUsers(keywordValue),
    ]);
    if (currentRequest !== requestId) return;
    items.value = (itemData.items || []).slice(0, 5);
    users.value = (userData.users || []).slice(0, 5);
  } catch (error) {
    if (currentRequest === requestId) session.notify(error.message, true);
  } finally {
    if (currentRequest === requestId) loading.value = false;
  }
}

function openItem(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
  closePanel();
}

async function submitSearch() {
  if (!trimmedKeyword.value) return;
  closePanel();
  await router.push(itemsRoute.value);
}
</script>

<style scoped>
.global-search-shell {
  position: sticky;
  top: 82px;
  z-index: 18;
  width: min(860px, 100%);
  justify-self: center;
}
.global-search {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 1px solid rgba(226, 232, 240, 0.88);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
}
.global-search-icon {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 999px;
  color: var(--primary-dark);
  background: rgba(20, 184, 166, 0.12);
  font-size: 20px;
  font-weight: 850;
}
.global-search input {
  min-height: 40px;
  padding: 0 4px;
  border: 0;
  background: transparent;
  box-shadow: none;
  font-size: 15px;
  font-weight: 650;
}
.global-search .btn { min-height: 40px; border-radius: 999px; padding: 8px 18px; }

.global-search-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow-xl);
  backdrop-filter: blur(20px);
}
.search-loading { grid-column: 1 / -1; padding: 18px; color: var(--muted); text-align: center; font-weight: 800; }
.search-result-group { display: grid; align-content: start; gap: 8px; min-width: 0; }
.search-panel-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 0 2px 4px; }
.search-panel-head strong { color: var(--ink); font-size: 14px; }

.search-result-row {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--ink);
  text-align: left;
  box-shadow: var(--shadow-sm);
  text-decoration: none;
}
.search-result-row:hover { transform: translateY(-1px); border-color: rgba(13, 148, 136, 0.22); box-shadow: var(--shadow-md); }
.search-result-row img { width: 46px; height: 46px; border-radius: 12px; object-fit: cover; background: var(--surface-soft); }
.search-result-row span { display: grid; gap: 3px; min-width: 0; }
.search-result-row strong, .search-result-row small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.search-result-row small { color: var(--muted); font-size: 12px; font-weight: 700; }
.search-result-row em { color: var(--accent-orange); font-style: normal; font-weight: 850; }
.user-result { grid-template-columns: 46px minmax(0, 1fr); }

.search-empty { margin: 0; padding: 14px; border: 1px dashed var(--line); border-radius: var(--radius-md); color: var(--muted); background: rgba(248, 250, 252, 0.78); font-size: 13px; font-weight: 750; text-align: center; }

@media (max-width: 620px) {
  .global-search-shell { top: 74px; }
  .global-search { grid-template-columns: auto minmax(0, 1fr); border-radius: var(--radius-lg); }
  .global-search .btn { grid-column: 1 / -1; width: 100%; }
  .global-search-panel { grid-template-columns: 1fr; }
}
</style>
