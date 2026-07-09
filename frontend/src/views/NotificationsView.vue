<template>
  <section v-if="!isUser()" class="empty-state"><strong>需要先登录</strong><RouterLink class="btn" to="/account">去登录</RouterLink></section>
  <template v-else>
    <section class="page-header animate-in">
      <div><h1>通知中心</h1><p class="muted">订单、留言、评价、认证审核和反馈回复都会在这里汇总。</p></div>
      <button class="ghost-btn" type="button" @click="readAll">全部已读</button>
    </section>
    <section class="table-list">
      <article v-for="item in notifications" :key="item.notificationNo" :class="['row-card', item.isRead ? '' : 'unread']">
        <div class="row-main">
          <strong>{{ item.title }}</strong>
          <span class="muted">{{ shortTime(item.createTime) }}</span>
        </div>
        <p>{{ item.content }}</p>
        <button v-if="!item.isRead" class="ghost-btn" type="button" @click="readOne(item.notificationNo)">标记已读</button>
      </article>
      <div v-if="!notifications.length" class="empty">暂无通知</div>
    </section>
  </template>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../api/client.js";
import { isUser, loadCommon, notify, state } from "../state/session.js";
import { shortTime } from "../utils.js";

const notifications = ref([]);
async function loadNotifications() {
  if (!isUser()) return;
  const data = await api("/api/notifications");
  notifications.value = data.notifications || [];
  state.unreadCount = data.unreadCount || 0;
}
async function readAll() {
  const data = await api("/api/notifications/read-all", { method: "POST", body: "{}" });
  notify(data.message);
  await loadNotifications();
  await loadCommon();
}
async function readOne(no) {
  const data = await api(`/api/notifications/${no}/read`, { method: "POST", body: "{}" });
  notify(data.message);
  await loadNotifications();
}
onMounted(loadNotifications);
</script>
