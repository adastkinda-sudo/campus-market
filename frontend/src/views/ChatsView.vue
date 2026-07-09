<template>
  <section v-if="!canTrade()" class="empty-state animate-in">
    <strong>私信仅面向已认证用户</strong>
    <p>请先完成校园身份认证后再使用私聊功能。</p>
    <RouterLink class="btn" to="/account">去认证</RouterLink>
  </section>

  <section v-else class="chat-layout animate-in">
    <aside class="band chat-list">
      <div class="section-head"><h2>私信</h2></div>
      <button v-for="conversation in conversations" :key="conversation.conversationNo" :class="['chat-list-item', activeConversationNo === conversation.conversationNo ? 'active' : '']" type="button" @click="selectConversation(conversation.conversationNo)">
        <img class="avatar" :src="conversation.otherAvatarUrl || '/assets/avatar-1.svg'" alt="" />
        <span>
          <strong>{{ conversation.otherName }}</strong>
          <small>{{ conversation.relatedItemTitle || "普通会话" }}</small>
          <small>{{ conversation.lastContent || "还没有消息" }}</small>
        </span>
        <em v-if="conversation.unreadCount">{{ conversation.unreadCount }}</em>
      </button>
      <div v-if="!conversations.length" class="empty">暂无私信</div>
    </aside>

    <section class="band chat-panel">
      <div class="section-head">
        <div>
          <h2>{{ otherUser?.nickname || "选择一个会话" }}</h2>
          <p v-if="otherUser" class="muted">{{ otherUser.userType }} · {{ otherUser.authStatus }}</p>
        </div>
      </div>
      <div class="chat-messages">
        <article v-for="message in messages" :key="message.privateMessageNo" :class="['chat-bubble', message.senderNo === state.principal.userNo ? 'mine' : '']">
          <strong>{{ message.senderName }}</strong>
          <p>{{ message.content }}</p>
          <span>{{ shortTime(message.sendTime) }}</span>
        </article>
        <div v-if="activeConversationNo && !messages.length" class="empty">还没有消息</div>
        <div v-if="!activeConversationNo" class="empty">从左侧选择会话，或在商品详情/用户主页发起私聊。</div>
      </div>
      <form v-if="activeConversationNo" class="chat-compose" @submit.prevent="sendMessage">
        <input v-model="messageText" placeholder="输入私聊内容" required />
        <button class="btn" type="submit">发送</button>
      </form>
    </section>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { api } from "../api/client.js";
import { canTrade, notify, state } from "../state/session.js";
import { shortTime } from "../utils.js";

const route = useRoute();
const router = useRouter();
const conversations = ref([]);
const messages = ref([]);
const otherUser = ref(null);
const activeConversationNo = ref(null);
const messageText = ref("");
let timer = null;

async function loadConversations() {
  if (!canTrade()) return;
  const data = await api("/api/chats");
  conversations.value = data.conversations || [];
  const queryConversation = Number(route.query.conversation || 0);
  if (queryConversation && !activeConversationNo.value) activeConversationNo.value = queryConversation;
  if (!activeConversationNo.value && conversations.value.length) activeConversationNo.value = conversations.value[0].conversationNo;
}

async function loadMessages() {
  if (!activeConversationNo.value) return;
  const data = await api(`/api/chats/${activeConversationNo.value}/messages`);
  messages.value = data.messages || [];
  otherUser.value = data.otherUser;
  await loadConversations();
}

async function selectConversation(no) {
  activeConversationNo.value = no;
  await router.replace({ path: "/chats", query: { conversation: no } });
  await loadMessages();
}

async function sendMessage() {
  try {
    const data = await api(`/api/chats/${activeConversationNo.value}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: messageText.value }),
    });
    notify(data.message);
    messageText.value = "";
    await loadMessages();
  } catch (error) {
    notify(error.message, true);
  }
}

watch(activeConversationNo, loadMessages);

onMounted(async () => {
  await loadConversations();
  await loadMessages();
  timer = window.setInterval(loadMessages, 5000);
});

onUnmounted(() => {
  if (timer) window.clearInterval(timer);
});
</script>
