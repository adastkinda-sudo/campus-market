<template>
  <section v-if="!session.isUser" class="empty-state animate-in">
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
import { getMyFeedback, submitFeedback as apiSubmitFeedback } from "../api/modules/contact.js";
import { useSessionStore } from "../stores/session.js";

const session = useSessionStore();

const form = reactive({ title: "", content: "" });
const feedback = ref([]);

async function loadFeedback() {
  if (!session.isUser) return;
  const data = await getMyFeedback();
  feedback.value = data.feedback || [];
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

onMounted(loadFeedback);
</script>
