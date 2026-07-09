<template>
  <section v-if="!session.isUser" class="empty-state"><strong>需要先登录</strong><RouterLink class="btn" to="/account">去登录</RouterLink></section>
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
import { getNotifications, readAll as apiReadAll, readOne as apiReadOne } from "../api/modules/notifications.js";
import { useCommonStore } from "../stores/common.js";
import { useSessionStore } from "../stores/session.js";
import { shortTime } from "../utils.js";

const session = useSessionStore();
const common = useCommonStore();

const notifications = ref([]);

async function loadNotifications() {
  if (!session.isUser) return;
  const data = await getNotifications();
  notifications.value = data.notifications || [];
  session.unreadCount = data.unreadCount || 0;
}

async function readAll() {
  try {
    const data = await apiReadAll();
    session.notify(data.message);
    await loadNotifications();
    await common.loadCommon();
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function readOne(no) {
  try {
    const data = await apiReadOne(no);
    session.notify(data.message);
    await loadNotifications();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadNotifications);
</script>
