<template>
  <section v-if="!session.isAdmin" class="empty-state animate-in">
    <strong>需要管理员权限</strong>
    <RouterLink class="btn" to="/account">去登录</RouterLink>
  </section>
  <template v-else>
    <section class="page-header animate-in">
      <div><h1>物品管理</h1><p class="muted">查看用户发布的物品，并处理违规或不适合展示的内容。</p></div>
      <button class="ghost-btn" type="button" @click="loadItems">刷新</button>
    </section>

    <section class="band animate-in delay-1">
      <div class="section-head">
        <h2>当前可见物品</h2>
        <span class="muted">{{ adminItems.length }} 件</span>
      </div>
      <div class="admin-item-grid">
        <article v-for="item in adminItems" :key="item.itemNo" class="admin-item-card">
          <div class="admin-item-thumb">
            <img :src="defaultImage(item)" :alt="item.title" />
          </div>
          <div class="admin-item-body">
            <div class="admin-item-head">
              <strong>{{ item.title }}</strong>
              <span class="price">{{ money(item.sellPrice) }}</span>
            </div>
            <div class="admin-item-meta" aria-label="卖家和物品归属信息">
              <p class="muted admin-item-seller" :title="`卖家 ${item.sellerName || '未知卖家'}`">卖家 {{ item.sellerName || "未知卖家" }}</p>
              <p class="muted admin-item-classify">
                <span>{{ item.categoryName || "未分类" }}</span>
                <span class="meta-dot">·</span>
                <span>{{ item.campusName || "校区未标注" }}</span>
              </p>
            </div>
            <div class="admin-item-tags" aria-label="物品状态信息">
              <span class="tag-slot"><span class="pill green">{{ item.status }}</span></span>
              <span class="tag-slot"><span class="pill">{{ item.condition }}</span></span>
              <span class="tag-slot"><span class="pill">浏览 {{ item.viewCount || 0 }}</span></span>
              <span class="tag-slot"><span class="pill gold">收藏 {{ item.favoriteCount || 0 }}</span></span>
            </div>
            <div class="actions">
              <button class="danger-btn" type="button" @click="deleteAdminItem(item)">删除物品</button>
            </div>
          </div>
        </article>
      </div>
      <div v-if="!adminItems.length" class="empty">暂无可管理物品</div>
    </section>
  </template>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { deleteItem, searchItems } from "../api/modules/items.js";
import { useSessionStore } from "../stores/session.js";
import { defaultImage, money } from "../utils.js";

const session = useSessionStore();
const adminItems = ref([]);

async function loadItems() {
  if (!session.isAdmin) return;
  try {
    const data = await searchItems({ status: "全部", sort: "new" });
    adminItems.value = data.items || [];
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function deleteAdminItem(item) {
  if (!window.confirm(`确定删除「${item.title}」吗？删除后该物品会从市场中隐藏，进行中的订单会被取消。`)) return;
  try {
    const data = await deleteItem(item.itemNo);
    session.notify(data.message);
    await loadItems();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadItems);
</script>

<style scoped>
.admin-item-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
  gap: 16px;
}
.admin-item-card {
  display: grid;
  grid-template-rows: auto min-content;
  align-content: start;
  gap: 10px;
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.admin-item-thumb {
  overflow: hidden;
  aspect-ratio: 4 / 3;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
}
.admin-item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.admin-item-body {
  display: grid;
  grid-template-rows: 48px auto 28px auto;
  align-content: start;
  gap: 6px;
  min-width: 0;
}
.admin-item-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: flex-start;
  gap: 8px;
  height: 48px;
  overflow: hidden;
}
.admin-item-head strong {
  display: -webkit-box;
  min-height: 2.56em;
  overflow-wrap: anywhere;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-height: 1.28;
}
.admin-item-meta {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.admin-item-meta p {
  margin: 0;
  min-width: 0;
  line-height: 1.35;
}
.admin-item-seller {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.admin-item-classify {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.admin-item-classify span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.admin-item-classify .meta-dot {
  flex: 0 0 auto;
  overflow: visible;
}
.admin-item-tags {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  align-items: center;
}
.tag-slot {
  display: flex;
  min-width: 0;
}
.tag-slot .pill {
  display: inline-flex;
  justify-content: center;
  width: 100%;
  min-width: 0;
  padding: 5px 5px;
  overflow: hidden;
  font-size: 12px;
  line-height: 1.2;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.admin-item-body .actions {
  align-self: start;
  margin-top: 0;
}
.admin-item-body .danger-btn {
  width: 100%;
}
@media (max-width: 980px) {
  .admin-item-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 620px) {
  .admin-item-grid { grid-template-columns: 1fr; }
}
</style>
