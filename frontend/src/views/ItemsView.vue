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
          <option v-for="category in common.categories" :key="category.categoryNo" :value="category.categoryNo">
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
      :show-favorite="session.isUser && item.sellerNo !== session.principal?.userNo"
      :show-buy="session.canTrade && item.sellerNo !== session.principal?.userNo && item.status === '在售'"
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
import { searchItems, toggleFavorite as apiToggleFavorite } from "../api/modules/items.js";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import ProductCard from "../components/ProductCard.vue";
import { useCommonStore } from "../stores/common.js";
import { useSessionStore } from "../stores/session.js";

const route = useRoute();
const session = useSessionStore();
const common = useCommonStore();

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

async function loadItems() {
  const params = new URLSearchParams();
  if (filters.keyword) params.set("keyword", filters.keyword);
  if (filters.categoryNo) params.set("categoryNo", filters.categoryNo);
  if (filters.campusName) params.set("campusName", filters.campusName);
  params.set("sort", filters.sort);
  try {
    const data = await searchItems(Object.fromEntries(params));
    items.value = data.items || [];
  } catch (error) {
    session.notify(error.message, true);
  }
}

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function toggleFavorite(item) {
  try {
    const data = await apiToggleFavorite(item.itemNo, item.isFavorite);
    session.notify(data.message);
    await loadItems();
  } catch (error) {
    session.notify(error.message, true);
  }
}

watch(() => route.query, syncQuery, { deep: true });
onMounted(() => {
  syncQuery();
  loadItems();
});
</script>
