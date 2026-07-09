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

<style scoped>
/* ===== Intro Hero ===== */
.intro-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(420px, 1.05fr);
  gap: 48px;
  min-height: 560px;
  padding: 64px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.48)), linear-gradient(180deg, rgba(240, 253, 250, 0.96), rgba(241, 245, 249, 0.92));
  box-shadow: var(--shadow-xl), var(--shadow-glow);
  backdrop-filter: blur(24px);
}
.intro-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(13, 148, 136, 0.06) 1px, transparent 1px), linear-gradient(180deg, rgba(59, 130, 246, 0.05) 1px, transparent 1px);
  background-size: 52px 52px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.65), transparent 88%);
  pointer-events: none;
}
.intro-hero::after {
  content: "";
  position: absolute;
  top: -40%;
  right: -20%;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.16), transparent 66%);
  pointer-events: none;
  filter: blur(20px);
}
.intro-copy, .intro-stage { position: relative; z-index: 1; }
.intro-copy { display: grid; align-content: center; justify-items: start; gap: 24px; }

.eyebrow {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  padding: 5px 12px;
  border: 1px solid rgba(13, 148, 136, 0.18);
  border-radius: 999px;
  color: var(--primary-dark);
  background: rgba(255, 255, 255, 0.62);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.intro-copy h1 {
  max-width: 720px;
  margin: 0;
  font-size: clamp(40px, 5vw, 58px);
  line-height: 1.05;
  letter-spacing: -0.03em;
  font-weight: 850;
  background: linear-gradient(135deg, var(--ink) 0%, var(--primary-dark) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.intro-copy p { max-width: 560px; margin: 0; color: var(--ink-soft); font-size: 17px; line-height: 1.75; }
.intro-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 6px; }
.intro-actions .btn, .intro-actions .ghost-btn { min-height: 46px; padding: 10px 22px; border-radius: 999px; font-size: 15px; }
.glass-button { background: rgba(255, 255, 255, 0.72); backdrop-filter: blur(14px); }

.intro-stage { min-height: 440px; display: grid; place-items: center; position: relative; }
.intro-stats { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 18px; }

/* ===== Preview Stage ===== */
.preview-stage { position: relative; width: 100%; max-width: 520px; aspect-ratio: 1 / 1; }
.preview-orbit {
  position: absolute;
  inset: 8%;
  border-radius: 50%;
  border: 1px dashed rgba(13, 148, 136, 0.18);
  animation: spin 36s linear infinite;
}
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.preview-window {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: var(--shadow-xl);
  backdrop-filter: blur(22px);
}
.preview-window-top {
  display: flex;
  gap: 7px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.7);
  background: rgba(255, 255, 255, 0.45);
}
.preview-window-top span { width: 10px; height: 10px; border-radius: 50%; background: #e2e8f0; }
.preview-window-top span:nth-child(1) { background: #fb7185; }
.preview-window-top span:nth-child(2) { background: #fbbf24; }
.preview-window-top span:nth-child(3) { background: #34d399; }
.preview-window-content { display: grid; gap: 14px; padding: 20px; }

.preview-row {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 14px;
  text-align: left;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.62);
  border: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: var(--shadow-sm);
}
.preview-row:hover { transform: translateY(-1px); border-color: rgba(13, 148, 136, 0.24); }
.preview-thumb {
  overflow: hidden;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.15), rgba(59, 130, 246, 0.12));
  display: grid;
  place-items: center;
  color: var(--primary);
  font-size: 24px;
}
.preview-thumb img { width: 100%; height: 100%; object-fit: cover; }
.preview-row-body { flex: 1; min-width: 0; }
.preview-row-title { font-weight: 800; color: var(--ink); margin-bottom: 4px; }
.preview-row-meta { color: var(--muted); font-size: 13px; font-weight: 600; }
.preview-price { font-size: 18px; font-weight: 850; color: var(--accent-orange); }
.preview-empty { padding: 28px; color: var(--muted); text-align: center; font-weight: 800; }

.preview-card {
  position: absolute;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
  width: 178px;
  padding: 11px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
  animation: float 5s ease-in-out infinite;
  pointer-events: none;
}
.preview-card-tools { left: 8px; top: 8px; animation-delay: 0s; }
.preview-card-order { right: 8px; top: 8px; animation-delay: 1.2s; }
.preview-card-icon {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  font-size: 20px;
  background: linear-gradient(135deg, rgba(20, 184, 166, 0.18), rgba(59, 130, 246, 0.12));
}
.preview-card strong, .preview-card span { display: block; }
.preview-card strong { font-weight: 800; color: var(--ink); font-size: 14px; }
.preview-card span { margin-top: 2px; color: var(--muted); font-size: 11px; font-weight: 600; }

.preview-dot {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 18px rgba(13, 148, 136, 0.45);
  animation: pulse-glow 2.4s ease-in-out infinite;
}
.preview-dot:nth-of-type(1) { top: 18%; right: 14%; }
.preview-dot:nth-of-type(2) { bottom: 28%; left: 10%; animation-delay: 0.8s; }
.preview-dot:nth-of-type(3) { top: 62%; right: 6%; animation-delay: 1.6s; background: var(--accent-blue); }

/* ===== Product Showcase ===== */
.product-showcase {
  padding: 22px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(16px);
}
.product-showcase-layout { display: grid; align-items: start; grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr); gap: 18px; }
.featured-product-stack { display: grid; gap: 18px; }

.featured-product {
  align-self: start;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(220px, 0.9fr) minmax(0, 1.1fr);
  min-height: 0;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: var(--shadow-lg);
}
.featured-product-stack .featured-product { min-height: 0; }
.featured-product-stack .featured-product-media { min-height: 220px; height: auto; }
.featured-product-stack .featured-product-body { align-content: start; gap: 10px; padding: 18px; }
.featured-product-stack .eyebrow, .featured-product-stack .product-metrics { display: none; }
.featured-product-stack .featured-product-body h2 { font-size: clamp(22px, 2vw, 26px); }
.featured-product-stack .featured-product-body p { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.featured-product-stack .actions { margin-top: 2px; }
.featured-product-stack .actions .btn, .featured-product-stack .actions .ghost-btn { min-height: 38px; padding: 8px 14px; white-space: nowrap; }

.featured-product-media {
  position: relative;
  overflow: hidden;
  height: clamp(240px, 28vw, 320px);
  background: linear-gradient(135deg, rgba(13, 148, 136, 0.12), rgba(59, 130, 246, 0.08)), #f8fafc;
}
.featured-product-media img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.35s ease; }
.featured-product:hover .featured-product-media img { transform: scale(1.04); }

.featured-badge {
  position: absolute;
  top: 14px;
  left: 14px;
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 5px 11px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, var(--primary-light), var(--primary));
  box-shadow: 0 8px 18px rgba(13, 148, 136, 0.22);
  font-size: 12px;
  font-weight: 850;
}
.featured-product-body { display: grid; align-content: center; gap: 13px; padding: 24px; }
.featured-product-body h2, .featured-product-body p { margin: 0; }
.featured-product-body h2 { font-size: clamp(24px, 2.4vw, 30px); line-height: 1.15; }
.featured-product-body p { color: var(--muted); }
.featured-price-row { display: flex; align-items: baseline; flex-wrap: wrap; gap: 9px; }
.product-metrics { display: flex; flex-wrap: wrap; gap: 8px; }
.product-metrics span { display: inline-flex; min-height: 26px; align-items: center; padding: 4px 10px; border-radius: 999px; color: var(--muted); background: var(--surface-soft); font-size: 12px; font-weight: 750; }

.product-side-panels { display: grid; gap: 16px; }
.showcase-panel {
  display: grid;
  align-content: start;
  gap: 13px;
  padding: 18px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-md);
}
.panel-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.panel-heading span { color: var(--ink-soft); font-size: 15px; font-weight: 850; }
.panel-heading strong { display: inline-grid; place-items: center; min-width: 30px; height: 30px; padding: 0 9px; border-radius: 999px; color: var(--primary-dark); background: #f0fdfa; font-size: 13px; }

.mini-product-list { display: grid; gap: 10px; }
.mini-product {
  display: grid;
  grid-template-columns: 58px minmax(0, 1fr) auto;
  align-items: center;
  gap: 11px;
  width: 100%;
  padding: 9px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: #fff;
  color: var(--ink);
  text-align: left;
  box-shadow: var(--shadow-sm);
}
.mini-product:hover { transform: translateY(-1px); border-color: rgba(13, 148, 136, 0.26); box-shadow: var(--shadow-md); }
.mini-product img { width: 58px; height: 58px; border-radius: var(--radius-sm); object-fit: cover; background: var(--surface-soft); }
.mini-product-main { display: grid; gap: 4px; min-width: 0; }
.mini-product-main strong, .mini-product-main span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mini-product-main strong { font-size: 13px; font-weight: 850; }
.mini-product-main span { color: var(--muted); font-size: 12px; font-weight: 650; }
.mini-product-price { color: var(--accent-orange); font-weight: 850; white-space: nowrap; }
.mini-empty { min-height: 82px; padding: 20px; }

/* ===== Glass Stats ===== */
.glass-stat {
  position: relative;
  overflow: hidden;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.62);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(20px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.glass-stat:hover { transform: translateY(-3px); box-shadow: var(--shadow-xl); }
.glass-stat span { display: block; color: var(--muted); font-size: 13px; font-weight: 700; }
.glass-stat strong { display: block; margin-top: 8px; font-size: 32px; line-height: 1; font-weight: 850; letter-spacing: -0.02em; color: var(--ink); }

/* ===== Feature Grid ===== */
.intro-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; }
.intro-feature {
  position: relative;
  overflow: hidden;
  display: grid;
  align-content: start;
  gap: 14px;
  min-height: 220px;
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(16px);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.intro-feature:hover { transform: translateY(-5px); box-shadow: var(--shadow-xl); border-color: rgba(13, 148, 136, 0.2); }
.intro-feature::after { content: ""; position: absolute; top: -40px; right: -40px; width: 120px; height: 120px; border-radius: 50%; background: radial-gradient(circle, rgba(13, 148, 136, 0.1), transparent 70%); }
.feature-icon { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 12px; background: linear-gradient(135deg, rgba(13, 148, 136, 0.12), rgba(59, 130, 246, 0.08)); color: var(--primary-dark); font-size: 20px; }
.intro-feature span { color: var(--primary-dark); font-size: 12px; font-weight: 850; letter-spacing: 0.04em; }
.intro-feature h2, .intro-feature p { margin: 0; }
.intro-feature h2 { font-size: 20px; font-weight: 800; }
.intro-feature p { color: var(--muted); line-height: 1.7; font-size: 14px; }

/* ===== Gallery ===== */
.intro-gallery {
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.6);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(16px);
}
.gallery-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.gallery-item {
  position: relative;
  overflow: hidden;
  display: block;
  aspect-ratio: 16 / 10;
  width: 100%;
  padding: 0;
  border: 1px solid rgba(226, 232, 240, 0.92);
  border-radius: var(--radius-md);
  color: inherit;
  text-align: left;
  background: #fff;
  box-shadow: var(--shadow-sm);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.gallery-item:hover { transform: translateY(-4px) scale(1.02); box-shadow: var(--shadow-lg); }
.gallery-item img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.35s ease; }
.gallery-item:hover img { transform: scale(1.08); }
.gallery-placeholder { width: 100%; height: 100%; display: grid; place-items: center; font-size: 36px; background: linear-gradient(135deg, rgba(13, 148, 136, 0.08), rgba(59, 130, 246, 0.06)); }
.gallery-caption {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: var(--radius-sm);
  color: #fff;
  background: rgba(15, 23, 42, 0.68);
  backdrop-filter: blur(12px);
}
.gallery-caption strong, .gallery-caption span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.gallery-caption strong { font-size: 14px; font-weight: 850; }
.gallery-caption span { color: rgba(255, 255, 255, 0.78); font-size: 12px; font-weight: 750; }

/* ===== Responsive ===== */
@media (max-width: 980px) {
  .intro-hero, .product-showcase-layout, .featured-product { grid-template-columns: 1fr; }
  .intro-hero { min-height: auto; padding: 42px; }
  .intro-copy h1 { font-size: 46px; }
  .intro-stage { min-height: 420px; }
  .intro-stats, .gallery-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .featured-product-media { height: 260px; }
  .featured-product-stack .featured-product { height: auto; }
  .featured-product-stack .featured-product-media { height: 240px; }
  .preview-stage { max-width: 420px; }
  .preview-card { width: 180px; }
  .preview-card-tools { left: 0; top: 0; }
  .preview-card-order { right: 0; top: 0; }
}
@media (max-width: 620px) {
  .intro-hero { padding: 26px; }
  .intro-copy h1 { font-size: 36px; }
  .intro-stage { min-height: auto; display: grid; place-items: center; }
  .preview-stage { max-width: 100%; aspect-ratio: 1 / 1.1; }
  .preview-card { position: relative; left: auto !important; right: auto !important; top: auto; bottom: auto; width: 100%; animation: none; }
  .preview-orbit, .preview-dot { display: none; }
  .intro-grid, .intro-stats, .gallery-strip { grid-template-columns: 1fr; }
  .mini-product { grid-template-columns: 52px minmax(0, 1fr); }
  .mini-product-price { grid-column: 2; }
}
@media (max-width: 620px) {
  .product-showcase, .intro-gallery { padding: 18px; }
  .featured-product-body { padding: 20px; }
}
</style>
