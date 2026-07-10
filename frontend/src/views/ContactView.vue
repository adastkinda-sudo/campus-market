<template>
  <template v-if="session.isAdmin">
    <section class="page-header animate-in">
      <div><h1>用户反馈</h1><p class="muted">查看用户提交的平台建议、异常问题，并直接回复处理结果。</p></div>
      <button class="ghost-btn" type="button" @click="loadAdminFeedback">刷新</button>
    </section>
    <section class="band animate-in delay-1">
      <div class="section-head"><h2>反馈处理</h2></div>
      <div class="table-list">
        <article v-for="item in adminFeedback" :key="item.feedbackNo" class="row-card">
          <div class="row-main"><strong>{{ item.title }}</strong><span class="pill gold">{{ item.feedbackStatus }}</span></div>
          <p class="muted">{{ item.userName }} · {{ item.userType }} · {{ item.authStatus }}</p>
          <p>{{ item.content }}</p>
          <form class="form-grid one" @submit.prevent="replyFeedback(item)">
            <label>管理员回复<textarea v-model="feedbackReplies[item.feedbackNo]" required /></label>
            <button class="btn" type="submit">{{ item.feedbackStatus === "已回复" ? "更新回复" : "回复用户" }}</button>
          </form>
        </article>
        <div v-if="!adminFeedback.length" class="empty">暂无用户反馈</div>
      </div>
    </section>
  </template>
  <section v-else-if="!session.isUser" class="empty-state animate-in">
    <strong>登录后可联系管理员</strong>
    <p>登录用户可以提交平台建议和使用反馈。</p>
    <RouterLink class="btn" to="/account">去登录</RouterLink>
  </section>
  <template v-else>
    <section class="page-header animate-in">
      <div><h1>联系我们</h1><p class="muted">提交平台建议、使用反馈或异常问题，管理员可直接回复。</p></div>
    </section>
    <section class="split">
      <div class="band">
        <div class="section-head"><h2>提交反馈</h2></div>
        <form class="form-grid one" @submit.prevent="submitFeedback">
          <label>标题<input v-model="form.title" required /></label>
          <label>反馈内容<textarea v-model="form.content" required /></label>
          <button class="btn" type="submit">提交反馈</button>
        </form>
      </div>
      <div class="band">
        <div class="section-head"><h2>我的反馈</h2></div>
        <div class="table-list">
          <article v-for="item in feedback" :key="item.feedbackNo" class="row-card">
            <div class="row-main"><strong>{{ item.title }}</strong><span class="pill gold">{{ item.feedbackStatus }}</span></div>
            <p>{{ item.content }}</p>
            <p v-if="item.reply" class="muted">管理员回复：{{ item.reply }}</p>
          </article>
          <div v-if="!feedback.length" class="empty">暂无反馈</div>
        </div>
      </div>
    </section>
  </template>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { getFeedback as getAdminFeedback, replyFeedback as apiReplyFeedback } from "../api/modules/admin.js";
import { getMyFeedback, submitFeedback as apiSubmitFeedback } from "../api/modules/contact.js";
import { useSessionStore } from "../stores/session.js";

const session = useSessionStore();

const form = reactive({ title: "", content: "" });
const feedback = ref([]);
const adminFeedback = ref([]);
const feedbackReplies = reactive({});

async function loadAdminFeedback() {
  if (!session.isAdmin) return;
  try {
    const data = await getAdminFeedback();
    adminFeedback.value = data.feedback || [];
    for (const item of adminFeedback.value) {
      feedbackReplies[item.feedbackNo] = item.reply || "";
    }
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function loadFeedback() {
  if (!session.isUser) return;
  try {
    const data = await getMyFeedback();
    feedback.value = data.feedback || [];
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function submitFeedback() {
  try {
    const data = await apiSubmitFeedback(form);
    session.notify(data.message);
    Object.assign(form, { title: "", content: "" });
    await loadFeedback();
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function replyFeedback(item) {
  try {
    const data = await apiReplyFeedback(item.feedbackNo, feedbackReplies[item.feedbackNo]);
    session.notify(data.message);
    await loadAdminFeedback();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(() => {
  if (session.isAdmin) loadAdminFeedback();
  else loadFeedback();
});
</script>
