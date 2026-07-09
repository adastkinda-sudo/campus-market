<template>
  <article :class="compact ? 'manage-card' : 'item-card'">
    <div :class="compact ? 'manage-thumb' : 'item-media'">
      <img :src="defaultImage(item)" :alt="item.title" />
      <span v-if="!compact" class="item-badge">{{ item.categoryName }}</span>
    </div>
    <div :class="compact ? 'manage-body' : 'item-body'">
      <div class="item-title">
        <h3>{{ item.title }}</h3>
      </div>
      <p v-if="!compact" class="item-desc">{{ truncateText(item.description, 58) }}</p>
      <div class="price-line">
        <span class="price">{{ money(item.sellPrice) }}</span>
        <span v-if="!compact && item.originalPrice > item.sellPrice" class="original-price">{{ money(item.originalPrice) }}</span>
        <span v-if="!compact && discountPercent(item)" class="discount-badge">{{ discountPercent(item) }}</span>
      </div>
      <div v-if="!compact" class="meta">
        <span class="pill green">{{ item.status }}</span>
        <span class="pill gold">{{ item.campusName || "校区未标注" }}</span>
        <span class="pill">{{ item.condition }}</span>
        <span class="pill">浏览 {{ item.viewCount || 0 }}</span>
        <span class="pill gold">信用 {{ item.creditScore }}</span>
      </div>
      <div v-if="!compact" class="muted item-seller">
        <RouterLink class="seller-link" :to="`/users/${item.sellerNo}`">卖家 {{ item.sellerName }}</RouterLink>
        <span> · 收藏 {{ item.favoriteCount || 0 }}</span>
      </div>
      <div class="actions">
        <button class="ghost-btn" type="button" @click="$emit('detail', item)">详情</button>
        <button v-if="editable" class="ghost-btn" type="button" @click="$emit('edit', item)">编辑</button>
        <button v-if="editable" class="danger-btn" type="button" @click="$emit('shelve', item)">下架</button>
        <button v-if="showFavorite" class="ghost-btn" type="button" @click="$emit('favorite', item)">{{ item.isFavorite ? "取消收藏" : "收藏" }}</button>
        <button v-if="showBuy" class="btn" type="button" @click="$emit('detail', item)">下单</button>
      </div>
    </div>
  </article>
</template>

<script setup>
import { RouterLink } from "vue-router";
import { defaultImage, discountPercent, money, truncateText } from "../utils.js";

defineProps({
  item: { type: Object, required: true },
  compact: Boolean,
  editable: Boolean,
  showFavorite: Boolean,
  showBuy: Boolean,
});
defineEmits(["detail", "edit", "shelve", "favorite"]);
</script>
