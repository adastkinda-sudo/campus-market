<template>
  <section v-if="!session.canTrade" class="empty-state animate-in">
    <strong>私信仅面向已认证用户</strong>
    <p>请先完成校园身份认证后再使用私聊功能。</p>
    <RouterLink class="btn" to="/account">去认证</RouterLink>
  </section>

  <section v-else class="chat-layout animate-in">
    <aside class="band chat-list">
      <div class="section-head"><h2>私信</h2></div>
      <button v-for="conversation in conversations" :key="conversation.conversationNo" :class="['chat-list-item', activeConversationNo === conversation.conversationNo ? 'active' : '']" type="button" @click="selectConversation(conversation.conversationNo)">
        <img class="avatar" :src="conversation.otherAvatarUrl || '/assets/default-avatar.svg'" alt="" />
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
        <article v-for="message in messages" :key="message.privateMessageNo" :class="['chat-bubble', message.senderNo === session.principal?.userNo ? 'mine' : '']">
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
import { createChat, getConversations, getMessages, sendMessage as apiSendMessage } from "../api/modules/chats.js";
import { useSessionStore } from "../stores/session.js";
import { shortTime } from "../utils.js";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const conversations = ref([]);
const messages = ref([]);
const otherUser = ref(null);
const activeConversationNo = ref(null);
const messageText = ref("");
let timer = null;

async function loadConversations() {
  if (!session.canTrade) return;
  const data = await getConversations();
  conversations.value = data.conversations || [];
  const queryConversation = Number(route.query.conversation || 0);
  if (queryConversation && !activeConversationNo.value) activeConversationNo.value = queryConversation;
  if (!activeConversationNo.value && conversations.value.length) activeConversationNo.value = conversations.value[0].conversationNo;
}

async function loadMessages() {
  if (!activeConversationNo.value) return;
  const data = await getMessages(activeConversationNo.value);
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
    await apiSendMessage(activeConversationNo.value, messageText.value);
    messageText.value = "";
    await loadMessages();
  } catch (error) {
    session.notify(error.message, true);
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

<style scoped>
.chat-layout { display: grid; grid-template-columns: minmax(260px, 340px) minmax(0, 1fr); gap: 22px; }
.chat-list, .chat-panel { min-height: 620px; }

.chat-list-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--ink);
  text-align: left;
  box-shadow: var(--shadow-sm);
}
.chat-list-item + .chat-list-item { margin-top: 10px; }
.chat-list-item.active { border-color: rgba(13, 148, 136, 0.28); background: #f0fdfa; }
.chat-list-item span, .chat-list-item small { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-list-item small { color: var(--muted); }
.chat-list-item em {
  display: inline-grid;
  place-items: center;
  min-width: 24px;
  height: 24px;
  border-radius: 999px;
  background: var(--red);
  color: white;
  font-style: normal;
  font-weight: 800;
}

.chat-messages {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 440px;
  max-height: 520px;
  overflow-y: auto;
  padding: 14px;
  border-radius: var(--radius-md);
  background: rgba(248, 250, 252, 0.8);
}
.chat-bubble { max-width: 72%; padding: 12px 14px; border-radius: var(--radius-md); background: #fff; box-shadow: var(--shadow-sm); }
.chat-bubble.mine { justify-self: end; background: #ccfbf1; }
.chat-bubble p { margin: 6px 0; }
.chat-bubble span { color: var(--muted); font-size: 12px; }
.chat-compose { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; margin-top: 14px; }
</style>
