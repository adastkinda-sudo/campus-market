<template>
  <BaseModal :model-value="modelValue" modal-class="detail-modal" @update:model-value="close">
    <div v-if="loading" class="empty">加载中...</div>
    <div v-else-if="item" class="detail-wrapper">
      <div class="detail-layout">
        <div class="detail-media">
          <img :src="defaultImage(item)" :alt="item.title" />
        </div>
        <div class="detail-body">
          <div class="section-head detail-head">
            <div>
              <h2>{{ item.title }}</h2>
              <div class="meta">
                <span class="pill green">{{ item.status }}</span>
                <span class="pill gold">{{ item.campusName || "校区未标注" }}</span>
                <span class="pill">{{ item.categoryName }}</span>
                <span class="pill">{{ item.condition }}</span>
              </div>
            </div>
            <span class="price">{{ money(item.sellPrice) }}</span>
          </div>
          <p>{{ item.description }}</p>
          <p class="muted seller-meta">
            卖家
            <RouterLink class="seller-link" :to="`/users/${item.sellerNo}`" @click="close">{{ item.sellerName }}</RouterLink>
            · 信用 {{ item.creditScore }} · 浏览 {{ item.viewCount }} · 收藏 {{ item.favoriteCount || 0 }}
          </p>
          <div class="actions">
            <button v-if="canFavorite" class="ghost-btn" type="button" @click="toggleFavorite">{{ item.isFavorite ? "取消收藏" : "收藏物品" }}</button>
            <button v-if="canBuy" class="btn" type="button" @click="showOrder = !showOrder">提交订单</button>
            <button v-if="canChat" class="ghost-btn" type="button" @click="startChat">私聊卖家</button>
          </div>
        </div>
      </div>

      <section v-if="showOrder && canBuy" class="band slim footer-actions">
        <h3>生成订单</h3>
        <form class="form-grid three" @submit.prevent="submitOrder">
          <label>交易校区
            <select v-model="orderForm.locationNo" required>
              <option v-for="location in common.locations" :key="location.locationNo" :value="location.locationNo">
                {{ location.campusName }}
              </option>
            </select>
          </label>
          <label>交易时间
            <input v-model="orderForm.meetTime" type="datetime-local" required />
          </label>
          <label>&nbsp;
            <button class="btn" type="submit">提交并锁定物品</button>
          </label>
        </form>
      </section>

      <section class="band slim footer-actions">
        <div class="section-head"><h3>留言</h3></div>
        <div class="table-list">
          <article v-for="message in messages" :key="message.messageNo" :class="['message', message.parentMessageNo ? 'reply' : '']">
            <div class="row-main">
              <strong>{{ message.userName }}</strong>
              <span class="muted">{{ shortTime(message.msgTime) }}</span>
            </div>
            <p>{{ message.content }}</p>
          </article>
          <div v-if="!messages.length" class="empty">暂无留言</div>
        </div>
        <form v-if="session.isUser" class="form-grid one footer-actions" @submit.prevent="submitMessage">
          <label>留言内容
            <textarea v-model="messageContent" required placeholder="询问细节、价格或面交安排"></textarea>
          </label>
          <button class="btn" type="submit">发布留言</button>
        </form>
        <div v-else-if="session.isAdmin" class="empty footer-actions">管理员可查看留言，不能以用户身份留言</div>
        <div v-else class="empty footer-actions">登录后可留言</div>
      </section>
    </div>
  </BaseModal>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { createChat } from "../api/modules/chats.js";
import { createMessage, createOrder, getItem, toggleFavorite as apiToggleFavorite } from "../api/modules/items.js";
import BaseModal from "./BaseModal.vue";
import { useCommonStore } from "../stores/common.js";
import { useSessionStore } from "../stores/session.js";
import { addBrowsingHistory, defaultImage, money, shortTime } from "../utils.js";

const props = defineProps({
  modelValue: Boolean,
  itemNo: Number,
});
const emit = defineEmits(["update:modelValue", "changed"]);

const router = useRouter();
const session = useSessionStore();
const common = useCommonStore();

const item = ref(null);
const messages = ref([]);
const loading = ref(false);
const showOrder = ref(false);
const messageContent = ref("");
const orderForm = reactive({ locationNo: "", meetTime: "" });

const own = computed(() => session.isUser && item.value?.sellerNo === session.principal?.userNo);
const canBuy = computed(() => session.canTrade && item.value && !own.value && item.value.status === "在售");
const canFavorite = computed(() => session.isUser && item.value && !own.value);
const canChat = computed(() => session.canTrade && item.value && !own.value);

watch(
  () => [props.modelValue, props.itemNo],
  async ([visible, itemNo]) => {
    if (visible && itemNo) await loadDetail(itemNo);
  },
  { immediate: true },
);

async function loadDetail(itemNo) {
  loading.value = true;
  try {
    const data = await getItem(itemNo);
    item.value = data.item;
    messages.value = data.messages || [];
    addBrowsingHistory(data.item);
    orderForm.locationNo = common.locations[0]?.locationNo || "";
  } catch (error) {
    session.notify(error.message, true);
    close();
  } finally {
    loading.value = false;
  }
}

function close() {
  emit("update:modelValue", false);
  item.value = null;
  messages.value = [];
  showOrder.value = false;
}

async function toggleFavorite() {
  try {
    const data = await apiToggleFavorite(item.value.itemNo, item.value.isFavorite);
    session.notify(data.message);
    await loadDetail(item.value.itemNo);
    emit("changed");
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function submitOrder() {
  try {
    const data = await createOrder(item.value.itemNo, orderForm);
    session.notify(data.message);
    await loadDetail(item.value.itemNo);
    emit("changed");
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function submitMessage() {
  try {
    const data = await createMessage(item.value.itemNo, messageContent.value);
    messageContent.value = "";
    session.notify(data.message);
    await loadDetail(item.value.itemNo);
  } catch (error) {
    session.notify(error.message, true);
  }
}

async function startChat() {
  try {
    const data = await createChat({ targetUserNo: item.value.sellerNo, relatedItemNo: item.value.itemNo });
    close();
    await router.push({ path: "/chats", query: { conversation: data.conversationNo } });
  } catch (error) {
    session.notify(error.message, true);
  }
}
</script>

<style scoped>
.detail-layout { display: grid; grid-template-columns: minmax(280px, 430px) minmax(0, 1fr); gap: 22px; min-width: 0; }
.detail-media {
  overflow: hidden;
  height: 320px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: #fff;
  box-shadow: var(--shadow-md);
}
.detail-media img { width: 100%; height: 100%; object-fit: cover; }
.detail-body { display: grid; align-content: start; gap: 14px; min-width: 0; }
.detail-body .section-head { align-items: flex-start; gap: 12px; margin-bottom: 0; }
.detail-body .detail-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; padding-right: 48px; }
.detail-body .section-head > div { min-width: 0; }
.detail-body .section-head .price { justify-self: end; margin-top: 2px; }
.detail-body h2 { overflow-wrap: anywhere; }
.seller-meta { margin: 0; }

@media (max-width: 980px) {
  .detail-layout { grid-template-columns: 1fr; }
  .detail-body .section-head { flex-direction: column; }
  .detail-body .detail-head { grid-template-columns: 1fr; padding-right: 0; }
  .detail-body .detail-head .price { justify-self: start; }
}
</style>
