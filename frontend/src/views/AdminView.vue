<template>
  <section v-if="!session.isAdmin" class="empty-state animate-in">
    <strong>需要管理员权限</strong>
    <RouterLink class="btn" to="/account">去登录</RouterLink>
  </section>
  <template v-else>
    <section class="page-header animate-in">
      <div><h1>后台管理</h1><p class="muted">审核认证、处理反馈、查看用户和运营状态。</p></div>
      <button class="ghost-btn" type="button" @click="loadAdmin">刷新</button>
    </section>

    <section class="stats">
      <div class="stat"><span class="muted">收藏总数</span><strong>{{ stats.totalFavorites || 0 }}</strong></div>
      <div class="stat"><span class="muted">未处理举报</span><strong>{{ stats.unreadReports || 0 }}</strong></div>
      <div class="stat"><span class="muted">订单状态数</span><strong>{{ stats.orders?.length || 0 }}</strong></div>
      <div class="stat"><span class="muted">物品状态数</span><strong>{{ stats.items?.length || 0 }}</strong></div>
    </section>

    <section class="band">
      <div class="section-head"><h2>身份认证审核</h2></div>
      <div class="table-list">
        <article v-for="user in authRequests" :key="user.userNo" class="row-card">
          <div class="row-main"><strong>{{ user.nickname }} · {{ user.realName }}</strong><span class="pill gold">{{ user.userType }}</span></div>
          <p class="muted">{{ user.studentNo }} · {{ user.phone || "未留手机" }} · {{ user.wechat || "未留微信" }}</p>
          <p>{{ user.bio || "无补充说明" }}</p>
          <img v-if="user.campusCardImageUrl" class="card-preview" :src="campusCardSrc(user.campusCardImageUrl)" alt="校园卡照片" />
          <div class="actions">
            <button class="btn" type="button" @click="auditUser(user.userNo, '已认证')">通过</button>
            <button class="danger-btn" type="button" @click="auditUser(user.userNo, '认证驳回')">驳回</button>
          </div>
        </article>
        <div v-if="!authRequests.length" class="empty">暂无待审核认证</div>
      </div>
    </section>

    <section class="band">
      <div class="section-head"><h2>用户反馈</h2></div>
      <div class="table-list">
        <article v-for="item in feedback" :key="item.feedbackNo" class="row-card">
          <div class="row-main"><strong>{{ item.title }}</strong><span class="pill gold">{{ item.feedbackStatus }}</span></div>
          <p class="muted">{{ item.userName }} · {{ item.userType }} · {{ item.authStatus }}</p>
          <p>{{ item.content }}</p>
          <form class="form-grid one" @submit.prevent="replyFeedback(item)">
            <label>回复<textarea v-model="feedbackReplies[item.feedbackNo]" :placeholder="item.reply || '输入管理员回复'" required /></label>
            <button class="btn" type="submit">回复</button>
          </form>
        </article>
        <div v-if="!feedback.length" class="empty">暂无反馈</div>
      </div>
    </section>

    <section class="band">
      <div class="section-head"><h2>用户管理</h2></div>
      <div class="table-list">
        <article v-for="user in users" :key="user.userNo" class="row-card">
          <div class="row-main"><strong>{{ user.nickname }} · {{ user.realName }}</strong><span :class="['pill', user.status === '正常' ? 'green' : 'red']">{{ user.status }}</span></div>
          <p class="muted">{{ user.userType }} · {{ user.authStatus }} · 信用 {{ user.creditScore }}</p>
          <div class="actions">
            <button class="ghost-btn" type="button" @click="setUserStatus(user.userNo, user.status === '正常' ? '封禁' : '正常')">{{ user.status === "正常" ? "封禁" : "恢复" }}</button>
          </div>
        </article>
      </div>
    </section>
  </template>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import {
  auditUser as apiAuditUser,
  getAuthRequests,
  getFeedback,
  getStats,
  getUsers,
  replyFeedback as apiReplyFeedback,
  setUserStatus as apiSetUserStatus,
} from "../api/modules/admin.js";
import { campusCardSrc } from "../api/modules/uploads.js";
import { useSessionStore } from "../stores/session.js";

const session = useSessionStore();

const authRequests = ref([]);
const feedback = ref([]);
const users = ref([]);
const stats = ref({});
const feedbackReplies = reactive({});

async function loadAdmin() {
  if (!session.isAdmin) return;
  const [authReq, fb, userList, statList] = await Promise.all([
    getAuthRequests(),
    getFeedback(),
    getUsers(),
    getStats(),
  ]);
  authRequests.value = authReq.authRequests || [];
  feedback.value = fb.feedback || [];
  users.value = userList.users || [];
  stats.value = statList;
}

async function auditUser(userNo, authStatus) {
  try {
    const data = await apiAuditUser(userNo, authStatus);
    session.notify(data.message);
    await loadAdmin();
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function replyFeedback(item) {
  try {
    const data = await apiReplyFeedback(item.feedbackNo, feedbackReplies[item.feedbackNo]);
    session.notify(data.message);
    await loadAdmin();
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function setUserStatus(userNo, status) {
  try {
    const data = await apiSetUserStatus(userNo, status);
    session.notify(data.message);
    await loadAdmin();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadAdmin);
</script>
