<template>
  <section v-if="!session.isUser" class="empty-state"><strong>需要先登录</strong><RouterLink class="btn" to="/account">去登录</RouterLink></section>
  <template v-else>
    <section class="page-header animate-in"><div><h1>我的订单</h1><p class="muted">买家提交订单后物品进入交易中，双方线下面交后确认完成。</p></div></section>
    <section class="table-list">
      <article v-for="order in orders" :key="order.orderNo" class="row-card order-row">
        <img class="order-thumb" :src="order.imageUrl || '/assets/kettle.svg'" alt="" />
        <div>
          <div class="row-main"><strong>{{ order.itemTitle }}</strong><span class="pill gold">{{ roleText(order) }}</span></div>
          <p class="muted">{{ order.campusName }} · {{ order.locationName }} · {{ shortTime(order.meetTime) }}</p>
          <div class="meta"><span class="pill green">{{ order.orderStatus }}</span><span class="pill">{{ money(order.orderAmount) }}</span></div>
          <div class="actions">
            <button v-if="canConfirm(order)" class="btn" type="button" @click="orderAction(order, 'confirm')">确认接单</button>
            <button v-if="canConfirm(order)" class="ghost-btn" type="button" @click="orderAction(order, 'reject')">拒绝</button>
            <button v-if="canComplete(order)" class="btn" type="button" @click="orderAction(order, 'complete')">确认收货</button>
            <button v-if="canCancel(order)" class="ghost-btn" type="button" @click="orderAction(order, 'cancel')">取消订单</button>
            <button v-if="canReview(order)" class="ghost-btn" type="button" @click="openReview(order)">评价</button>
          </div>
        </div>
      </article>
      <div v-if="!orders.length" class="empty">暂无订单</div>
    </section>
  </template>
  <BaseModal v-model="reviewOpen">
    <section class="band slim">
      <div class="section-head"><h2>提交评价</h2></div>
      <form class="form-grid one" @submit.prevent="submitReview">
        <label>评分<select v-model="reviewForm.rating"><option v-for="n in 5" :key="n" :value="n">{{ n }} 星</option></select></label>
        <label>评价内容<textarea v-model="reviewForm.content" required /></label>
        <button class="btn" type="submit">提交评价</button>
      </form>
    </section>
  </BaseModal>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { createReview, getMyOrders, orderAction as apiOrderAction } from "../api/modules/orders.js";
import BaseModal from "../components/BaseModal.vue";
import { useSessionStore } from "../stores/session.js";
import { money, shortTime } from "../utils.js";

const session = useSessionStore();

const orders = ref([]);
const reviewOpen = ref(false);
const reviewForm = reactive({ orderNo: null, rating: 5, content: "" });

function roleText(order) { return order.buyerNo === session.principal?.userNo ? "我买入" : "我售出"; }
function canConfirm(order) { return order.sellerNo === session.principal?.userNo && order.orderStatus === "待卖家确认"; }
function canComplete(order) { return order.buyerNo === session.principal?.userNo && order.orderStatus === "待面交"; }
function canCancel(order) { return ["待卖家确认", "待面交"].includes(order.orderStatus); }
function canReview(order) { return order.orderStatus === "交易成功" && !order.reviewedByMe; }

async function loadOrders() {
  if (!session.isUser) return;
  const data = await getMyOrders();
  orders.value = data.orders || [];
}

async function orderAction(order, action) {
  try {
    const data = await apiOrderAction(order.orderNo, action);
    session.notify(data.message);
    await loadOrders();
  } catch (error) {
    session.notify(error.message, true);
  }
}

function openReview(order) {
  Object.assign(reviewForm, { orderNo: order.orderNo, rating: 5, content: "" });
  reviewOpen.value = true;
}

async function submitReview() {
  try {
    const data = await createReview(reviewForm.orderNo, reviewForm);
    session.notify(data.message);
    reviewOpen.value = false;
    await loadOrders();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadOrders);
</script>

<style scoped>
.order-row { display: grid; grid-template-columns: 104px minmax(0, 1fr); gap: 16px; }
.order-thumb { width: 100%; height: 96px; border-radius: var(--radius-sm); border: 1px solid var(--line); object-fit: cover; }
@media (max-width: 620px) {
  .order-row { grid-template-columns: 1fr; }
  .order-thumb { height: 160px; }
}
</style>
