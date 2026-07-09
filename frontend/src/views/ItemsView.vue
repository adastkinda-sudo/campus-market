<template>
  <section class="page-header animate-in">
    <div>
      <h1>浏览物品</h1>
      <p class="muted">支持游客浏览，登录认证后可下单、收藏、留言和私聊。</p>
    </div>
  </section>

  <section class="band animate-in delay-1">
    <form class="form-grid" @submit.prevent="loadItems">
      <label>关键词
        <input v-model="filters.keyword" placeholder="搜索标题、描述、卖家或校区" />
      </label>
      <label>分类
        <select v-model="filters.categoryNo">
          <option value="">全部分类</option>
          <option v-for="category in state.categories" :key="category.categoryNo" :value="category.categoryNo">
            {{ category.parentCategoryName ? `${category.parentCategoryName} / ${category.categoryName}` : category.categoryName }}
          </option>
        </select>
      </label>
      <label>校区
        <select v-model="filters.campusName">
          <option value="">全部校区</option>
          <option>徐汇校区</option>
          <option>奉贤校区</option>
        </select>
      </label>
      <label>排序
        <select v-model="filters.sort">
          <option value="new">最新发布</option>
          <option value="price_asc">价格从低到高</option>
          <option value="price_desc">价格从高到低</option>
          <option value="hot">浏览最多</option>
        </select>
      </label>
      <button class="btn" type="submit">搜索</button>
    </form>
  </section>

  <section v-if="items.length" class="item-grid animate-in delay-2">
    <ProductCard
      v-for="item in items"
      :key="item.itemNo"
      :item="item"
      :show-favorite="isUser() && item.sellerNo !== state.principal?.userNo"
      :show-buy="canTrade() && item.sellerNo !== state.principal?.userNo && item.status === '在售'"
      @detail="openDetail"
      @favorite="toggleFavorite"
    />
  </section>
  <section v-else class="empty-state animate-in delay-2">
    <span class="icon">⌕</span>
    <strong>暂无符合条件的物品</strong>
  </section>

  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadItems" />
</template>

<script setup>
import { onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api/client.js";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import ProductCard from "../components/ProductCard.vue";
import { canTrade, isUser, notify, state } from "../state/session.js";

const route = useRoute();
const items = ref([]);
const detailOpen = ref(false);
const activeItemNo = ref(null);
const filters = reactive({
  keyword: "",
  categoryNo: "",
  campusName: "",
  sort: "new",
});

function syncQuery() {
  filters.keyword = route.query.keyword || "";
  filters.categoryNo = route.query.categoryNo || "";
}

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadItems() {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  try {
    const data = await api(`/api/items?${params.toString()}`);
    items.value = data.items || [];
  } catch (error) {
    notify(error.message, true);
  }
}

async function toggleFavorite(item) {
  try {
    const data = await api(`/api/items/${item.itemNo}/favorite`, {
      method: item.isFavorite ? "DELETE" : "POST",
    });
    notify(data.message);
    await loadItems();
  } catch (error) {
    notify(error.message, true);
  }
}

watch(() => [route.query.keyword, route.query.categoryNo], async () => {
  syncQuery();
  await loadItems();
});

onMounted(async () => {
  syncQuery();
  await loadItems();
});
</script>
