<template>
  <section v-if="user" class="page-header animate-in profile-hero">
    <img class="avatar-lg" :src="user.avatarUrl || '/assets/default-avatar.svg'" alt="" />
    <div>
      <h1>{{ user.nickname }}</h1>
      <p class="muted">{{ user.userType }} · {{ user.authStatus }} · 信用 {{ user.creditScore }}</p>
      <p>{{ user.bio || "这个人还没有写个性签名。" }}</p>
    </div>
    <button v-if="canChatUser" class="btn" type="button" @click="startChat">私聊</button>
  </section>

  <section v-if="user" class="band animate-in delay-1">
    <div class="stats">
      <div class="stat"><span class="muted">身份认证</span><strong>{{ user.authStatus }}</strong></div>
      <div class="stat"><span class="muted">身份类型</span><strong>{{ user.userType }}</strong></div>
      <div class="stat"><span class="muted">入学年份</span><strong>{{ user.entryYear || "未填写" }}</strong></div>
      <div class="stat"><span class="muted">出售商品</span><strong>{{ items.length }}</strong></div>
    </div>
  </section>

  <section class="band animate-in delay-2">
    <div class="section-head"><h2>出售过的商品</h2></div>
    <div v-if="items.length" class="item-grid">
      <ProductCard v-for="item in items" :key="item.itemNo" :item="item" @detail="openDetail" />
    </div>
    <div v-else class="empty">暂无公开商品</div>
  </section>

  <section class="band animate-in delay-3">
    <div class="section-head"><h2>商品下的评论</h2></div>
    <div class="table-list">
      <article v-for="message in messages" :key="message.messageNo" class="message">
        <div class="row-main"><strong>{{ message.itemTitle }}</strong><span class="muted">{{ shortTime(message.msgTime) }}</span></div>
        <p>{{ message.userName }}：{{ message.content }}</p>
      </article>
      <div v-if="!messages.length" class="empty">暂无评论</div>
    </div>
  </section>

  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadProfile" />
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { createChat } from "../api/modules/chats.js";
import { getUserProfile } from "../api/modules/users.js";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import ProductCard from "../components/ProductCard.vue";
import { useSessionStore } from "../stores/session.js";
import { shortTime } from "../utils.js";

const route = useRoute();
const router = useRouter();
const session = useSessionStore();

const user = ref(null);
const items = ref([]);
const messages = ref([]);
const detailOpen = ref(false);
const activeItemNo = ref(null);
const canChatUser = computed(() => session.canTrade && user.value && user.value.userNo !== session.principal?.userNo && user.value.authStatus === "已认证");

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadProfile() {
  try {
    const data = await getUserProfile(route.params.id);
    user.value = data.user;
    items.value = data.items || [];
    messages.value = data.messages || [];
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function startChat() {
  try {
    const data = await createChat({ targetUserNo: user.value.userNo });
    await router.push({ path: "/chats", query: { conversation: data.conversationNo } });
  } catch (error) {
    session.notify(error.message, true);
  }
}

watch(() => route.params.id, loadProfile);
onMounted(loadProfile);
</script>
