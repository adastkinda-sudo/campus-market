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
            <img :src="user.avatarUrl || '/assets/avatar-1.svg'" alt="" />
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
