<template>
  <section class="intro-hero animate-in">
    <div class="intro-copy">
      <span class="eyebrow">ECUST C2C Marketplace</span>
      <h1>让华理闲置<br />重新流动起来</h1>
      <p>面向华东理工大学徐汇校区、奉贤校区学生、教职工与校友的校内交易平台。发布、浏览、求购、下单锁定、线下面交、评价与风控，全流程一站式完成。</p>
      <div class="intro-actions">
        <RouterLink class="btn" to="/items">进入交易市场</RouterLink>
        <RouterLink class="ghost-btn glass-button" to="/publish">发布闲置</RouterLink>
      </div>
    </div>
    <div class="intro-stage" aria-label="系统功能预览">
      <div class="preview-stage">
        <div class="preview-orbit"></div>
        <div class="preview-window">
          <div class="preview-window-top"><span></span><span></span><span></span></div>
          <div class="preview-window-content">
            <button v-for="item in previewItems" :key="item.itemNo" class="preview-row" type="button" @click="openDetail(item)">
              <div class="preview-thumb"><img :src="defaultImage(item)" alt="" /></div>
              <div class="preview-row-body">
                <div class="preview-row-title">{{ item.title }}</div>
                <div class="preview-row-meta">{{ item.campusName }} · {{ item.condition }} · 信用 {{ item.creditScore }}</div>
              </div>
              <span class="preview-price">{{ money(item.sellPrice) }}</span>
            </button>
          </div>
        </div>
        <div class="preview-card preview-card-tools">
          <div class="preview-card-icon">🚲</div>
          <div><strong>代步工具</strong><span>校内通勤好物</span></div>
        </div>
        <div class="preview-card preview-card-order">
          <div class="preview-card-icon">🔒</div>
          <div><strong>订单锁定</strong><span>避免多人同时下单</span></div>
        </div>
      </div>
    </div>
  </section>

  <section v-if="common.announcements.length" class="announcement-banner animate-in">
    <strong>{{ common.announcements[0].title }}</strong>
    <span>{{ common.announcements[0].content }}</span>
  </section>

  <section class="category-strip animate-in">
    <button v-for="category in parentCategories" :key="category.categoryNo" class="category-chip" type="button" @click="$router.push({ path: '/items', query: { categoryNo: category.categoryNo } })">
      <strong>{{ category.categoryName }}</strong>
      <span>{{ category.itemCount || 0 }} 件</span>
    </button>
  </section>

  <section v-if="featuredItems.length" class="product-showcase animate-in">
    <div class="section-head">
      <h2>商品精选展示</h2>
      <RouterLink class="ghost-btn" to="/items">进入市场</RouterLink>
    </div>
    <div class="product-showcase-layout">
      <div class="featured-product-stack">
        <article v-for="(item, index) in featuredItems" :key="item.itemNo" class="featured-product">
          <div class="featured-product-media">
            <img :src="defaultImage(item)" :alt="item.title" />
            <span class="featured-badge">{{ index ? "精选好物" : "重点推荐" }}</span>
          </div>
          <div class="featured-product-body">
            <span class="eyebrow">Featured Item</span>
            <h2>{{ item.title }}</h2>
            <p>{{ truncateText(item.description, 92) }}</p>
            <div class="featured-price-row">
              <span class="price">{{ money(item.sellPrice) }}</span>
              <span v-if="item.originalPrice > item.sellPrice" class="original-price">{{ money(item.originalPrice) }}</span>
              <span v-if="discountPercent(item)" class="discount-badge">{{ discountPercent(item) }}</span>
            </div>
            <div class="meta">
              <span class="pill green">{{ item.status }}</span>
              <span class="pill gold">{{ item.campusName }}</span>
              <span class="pill">{{ item.condition }}</span>
              <span class="pill">{{ item.categoryName }}</span>
              <span class="pill gold">信用 {{ item.creditScore }}</span>
            </div>
            <div class="actions">
              <button class="btn" type="button" @click="openDetail(item)">查看详情</button>
              <RouterLink class="ghost-btn" :to="{ path: '/items', query: { categoryNo: item.categoryNo } }">看同类商品</RouterLink>
            </div>
          </div>
        </article>
      </div>
      <div class="product-side-panels">
        <article class="showcase-panel">
          <div class="panel-heading"><span>热门关注</span><strong>{{ hotItems.length }}</strong></div>
          <button v-for="item in hotItems" :key="item.itemNo" class="mini-product" type="button" @click="openDetail(item)">
            <img :src="defaultImage(item)" alt="" />
            <span class="mini-product-main"><strong>{{ item.title }}</strong><span>{{ item.campusName }} · {{ item.condition }}</span></span>
            <span class="mini-product-price">{{ money(item.sellPrice) }}</span>
          </button>
        </article>
        <article class="showcase-panel">
          <div class="panel-heading"><span>实惠专区</span><strong>{{ dealItems.length }}</strong></div>
          <button v-for="item in dealItems" :key="item.itemNo" class="mini-product" type="button" @click="openDetail(item)">
            <img :src="defaultImage(item)" alt="" />
            <span class="mini-product-main"><strong>{{ item.title }}</strong><span>{{ item.campusName }} · {{ item.condition }}</span></span>
            <span class="mini-product-price">{{ money(item.sellPrice) }}</span>
          </button>
        </article>
      </div>
    </div>
  </section>

  <section class="intro-stats">
    <div class="glass-stat"><span>平台物品</span><strong>{{ common.dashboard?.itemCount || 0 }}</strong></div>
    <div class="glass-stat"><span>正在出售</span><strong>{{ common.dashboard?.onSaleCount || 0 }}</strong></div>
    <div class="glass-stat"><span>注册用户</span><strong>{{ common.dashboard?.userCount || 0 }}</strong></div>
    <div class="glass-stat"><span>成功订单</span><strong>{{ common.dashboard?.successOrderCount || 0 }}</strong></div>
  </section>

  <section v-if="latestItems.length" class="intro-gallery animate-in">
    <div class="section-head">
      <h2>商品橱窗</h2>
      <RouterLink class="ghost-btn" to="/items">查看全部</RouterLink>
    </div>
    <div class="gallery-strip">
      <button v-for="item in latestItems.slice(0, 4)" :key="item.itemNo" class="gallery-item" type="button" @click="openDetail(item)">
        <img :src="defaultImage(item)" :alt="item.title" />
        <span class="gallery-caption">
          <strong>{{ item.title }}</strong>
          <span>{{ money(item.sellPrice) }} · {{ item.condition }}</span>
        </span>
      </button>
    </div>
  </section>

  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadHome" />
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { searchItems } from "../api/modules/items.js";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import { useCommonStore } from "../stores/common.js";
import { useSessionStore } from "../stores/session.js";
import { defaultImage, discountPercent, money, truncateText } from "../utils.js";

const session = useSessionStore();
const common = useCommonStore();

const latestItems = ref([]);
const hotItems = ref([]);
const detailOpen = ref(false);
const activeItemNo = ref(null);

const featuredItems = computed(() => hotItems.value.slice(0, 2));
const dealItems = computed(() => latestItems.value.filter((item) => Number(item.sellPrice) <= 100).slice(0, 4));
const previewItems = computed(() => latestItems.value.slice(0, 4));
const parentCategories = computed(() => common.categories.filter((category) => !category.parentCategoryNo).slice(0, 8));

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadHome() {
  try {
    const [latest, hot] = await Promise.all([
      searchItems({ sort: "new" }),
      searchItems({ sort: "hot" }),
    ]);
    latestItems.value = latest.items || [];
    hotItems.value = hot.items || [];
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadHome);
</script>
