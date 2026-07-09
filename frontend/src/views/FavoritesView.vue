<template>
  <section v-if="!isUser()" class="empty-state animate-in">
    <strong>需要先登录</strong>
    <RouterLink class="btn" to="/account">去登录</RouterLink>
  </section>
  <template v-else>
    <section class="page-header animate-in"><h1>我的收藏</h1></section>
    <section v-if="items.length" class="item-grid">
      <ProductCard v-for="item in items" :key="item.itemNo" :item="item" show-favorite @detail="openDetail" @favorite="toggleFavorite" />
    </section>
    <section v-else class="empty-state"><strong>暂无收藏</strong></section>
  </template>
  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadFavorites" />
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../api/client.js";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import ProductCard from "../components/ProductCard.vue";
import { isUser, notify } from "../state/session.js";

const items = ref([]);
const detailOpen = ref(false);
const activeItemNo = ref(null);

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadFavorites() {
  if (!isUser()) return;
  try {
    const data = await api("/api/favorites");
    items.value = data.items || [];
  } catch (error) {
    notify(error.message, true);
  }
}

async function toggleFavorite(item) {
  try {
    const data = await api(`/api/items/${item.itemNo}/favorite`, { method: "DELETE" });
    notify(data.message);
    await loadFavorites();
  } catch (error) {
    notify(error.message, true);
  }
}

onMounted(loadFavorites);
</script>
