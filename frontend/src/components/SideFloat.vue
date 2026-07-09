<template>
  <div class="side-float">
    <button v-if="session.canTrade" class="float-btn" type="button" title="私信客服" @click="openSupportChat">
      <span class="float-icon">💬</span>
      <span class="float-text">客服</span>
    </button>
    <RouterLink v-else class="float-btn" to="/contact" title="联系客服">
      <span class="float-icon">💬</span>
      <span class="float-text">客服</span>
    </RouterLink>
    <RouterLink class="float-btn" to="/contact" title="意见反馈">
      <span class="float-icon">📝</span>
      <span class="float-text">反馈</span>
    </RouterLink>
    <button v-if="showTop" class="float-btn" type="button" title="回到顶部" @click="scrollToTop">
      <span class="float-icon">⬆</span>
      <span class="float-text">顶部</span>
    </button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { searchUsers } from "../api/modules/users.js";
import { createChat } from "../api/modules/chats.js";
import { useSessionStore } from "../stores/session.js";

const router = useRouter();
const session = useSessionStore();

const showTop = ref(false);
let supportUserNo = null;

async function openSupportChat() {
  try {
    if (!supportUserNo) {
      const data = await searchUsers("校园客服");
      const support = (data.users || []).find((u) => u.nickname === "校园客服");
      if (support) supportUserNo = support.userNo;
    }
    if (supportUserNo) {
      const chat = await createChat({ targetUserNo: supportUserNo });
      await router.push({ path: "/chats", query: { conversation: chat.conversationNo } });
    } else {
      await router.push("/chats");
    }
  } catch {
    await router.push("/chats");
  }
}

function onScroll() {
  showTop.value = window.scrollY > 300;
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
});

onUnmounted(() => {
  window.removeEventListener("scroll", onScroll);
});
</script>

<style scoped>
.side-float {
  position: fixed;
  right: 20px;
  bottom: 100px;
  z-index: 30;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.float-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 52px;
  height: 52px;
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--ink-soft);
  text-decoration: none;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: all 0.16s ease;
  backdrop-filter: blur(12px);
}
.float-btn:hover {
  transform: translateY(-2px);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: var(--shadow-lg);
}
.float-icon { font-size: 18px; line-height: 1; }
.float-text { font-size: 11px; }

@media (max-width: 720px) {
  .side-float { right: 10px; bottom: 80px; }
  .float-btn { width: 44px; height: 44px; }
}
</style>
