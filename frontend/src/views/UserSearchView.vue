<template>
  <section class="page-header animate-in">
    <div><h1>用户搜索</h1><p class="muted">搜索昵称、真实姓名或学号/工号，查看公开主页、身份认证和出售过的商品。</p></div>
  </section>
  <section class="band">
    <form class="form-grid three" @submit.prevent="loadUsers">
      <label>关键词<input v-model="keyword" placeholder="输入昵称、姓名或学号/工号" /></label>
      <button class="btn" type="submit">搜索</button>
    </form>
  </section>
  <section v-if="searched && users.length" class="item-grid">
    <RouterLink v-for="user in users" :key="user.userNo" class="user-card" :to="`/users/${user.userNo}`">
      <img class="avatar" :src="user.avatarUrl || '/assets/avatar-1.svg'" alt="" />
      <div>
        <h3>{{ user.nickname }}</h3>
        <p class="muted">{{ user.userType }} · {{ user.authStatus }} · 信用 {{ user.creditScore }}</p>
        <p>{{ user.bio || "这个人还没有写个性签名。" }}</p>
      </div>
    </RouterLink>
  </section>
  <section v-else class="empty-state">
    <span class="icon">⌕</span>
    <strong>{{ searched ? "没有找到相关用户" : "输入关键词后查看用户结果" }}</strong>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { api } from "../api/client.js";
import { notify } from "../state/session.js";

const route = useRoute();
const keyword = ref("");
const users = ref([]);
const searched = ref(false);

async function loadUsers() {
  const value = keyword.value.trim();
  searched.value = true;
  if (!value) {
    users.value = [];
    return;
  }
  try {
    const data = await api(`/api/users?keyword=${encodeURIComponent(value)}`);
    users.value = data.users || [];
  } catch (error) {
    notify(error.message, true);
  }
}

async function syncQuery() {
  keyword.value = route.query.keyword || "";
  if (keyword.value) {
    await loadUsers();
  } else {
    searched.value = false;
    users.value = [];
  }
}

watch(() => route.query.keyword, syncQuery);
onMounted(syncQuery);
</script>
