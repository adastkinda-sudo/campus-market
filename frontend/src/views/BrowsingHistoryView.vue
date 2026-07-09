<template>
  <section class="page-header animate-in">
    <h1>浏览记录</h1>
  </section>
  <section v-if="items.length" class="item-grid">
    <button v-for="item in items" :key="item.itemNo" class="showcase-card" type="button" @click="openDetail(item.itemNo)">
      <div class="showcase-card-media">
        <img :src="item.imageUrl" :alt="item.title" />
      </div>
      <div class="showcase-card-body">
        <strong class="showcase-card-title">{{ item.title }}</strong>
        <div class="showcase-card-footer">
          <span class="price">{{ money(item.sellPrice) }}</span>
          <span class="showcase-fav-count">{{ shortTime(item.viewTime) }}</span>
        </div>
      </div>
    </button>
  </section>
  <section v-else class="empty-state">
    <span class="icon">👀</span>
    <strong>暂无浏览记录</strong>
    <p>点开商品详情后会出现在这里</p>
  </section>
  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadHistory" />
</template>

<script setup>
import { onMounted, ref } from "vue";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import { getBrowsingHistory } from "../utils.js";
import { money, shortTime } from "../utils.js";

const items = ref([]);
const detailOpen = ref(false);
const activeItemNo = ref(null);

function openDetail(itemNo) {
  activeItemNo.value = itemNo;
  detailOpen.value = true;
}

function loadHistory() {
  items.value = getBrowsingHistory();
}

onMounted(loadHistory);
</script>
