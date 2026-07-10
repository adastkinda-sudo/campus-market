<template>
  <section class="intro-hero animate-in">
    <div class="intro-copy">
      <span class="eyebrow">ECUST C2C Marketplace</span>
      <h1>让闲置好物<br />在华理再次流转</h1>
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

  <section v-if="showcaseItems.length" class="product-showcase animate-in">
    <div class="section-head">
      <h2>热门商品</h2>
      <RouterLink class="ghost-btn" to="/items">进入市场</RouterLink>
    </div>
    <div class="showcase-tabs">
      <button
        :class="['showcase-tab', activeCategory === null ? 'active' : '']"
        type="button"
        @click="activeCategory = null"
      >全部</button>
      <button
        v-for="category in parentCategories"
        :key="category.categoryNo"
        :class="['showcase-tab', activeCategory === category.categoryNo ? 'active' : '']"
        type="button"
        @click="activeCategory = category.categoryNo"
      >
        {{ category.categoryName }}
      </button>
    </div>
    <div v-if="filteredShowcaseItems.length" class="showcase-grid">
      <button v-for="item in filteredShowcaseItems" :key="item.itemNo" class="showcase-card" type="button" @click="openDetail(item)">
        <div class="showcase-card-media">
          <img :src="defaultImage(item)" :alt="item.title" />
        </div>
        <div class="showcase-card-body">
          <strong class="showcase-card-title">{{ item.title }}</strong>
          <div class="showcase-card-footer">
            <span class="price">{{ money(item.sellPrice) }}</span>
            <span class="showcase-fav-count">收藏 {{ item.favoriteCount || 0 }}</span>
          </div>
        </div>
      </button>
    </div>
    <div v-else class="empty">该分类暂无商品</div>
  </section>

  <section class="intro-stats">
    <div class="glass-stat"><span>平台物品</span><strong>{{ common.dashboard?.itemCount || 0 }}</strong></div>
    <div class="glass-stat"><span>正在出售</span><strong>{{ common.dashboard?.onSaleCount || 0 }}</strong></div>
    <div class="glass-stat"><span>注册用户</span><strong>{{ common.dashboard?.userCount || 0 }}</strong></div>
    <div class="glass-stat"><span>成功订单</span><strong>{{ common.dashboard?.successOrderCount || 0 }}</strong></div>
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
import { defaultImage, money } from "../utils.js";

const session = useSessionStore();
const common = useCommonStore();

const hotItems = ref([]);
const activeCategory = ref(null);
const detailOpen = ref(false);
const activeItemNo = ref(null);

const showcaseItems = computed(() => hotItems.value.slice(0, 8));
const filteredShowcaseItems = computed(() => {
  const items = activeCategory.value === null ? hotItems.value : hotItems.value.filter(
    (item) => item.categoryNo === activeCategory.value || item.parentCategoryNo === activeCategory.value
  );
  return items.slice(0, 8);
});
const previewItems = computed(() => hotItems.value.slice(0, 4));
const parentCategories = computed(() => common.categories.filter((category) => !category.parentCategoryNo).slice(0, 8));

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadHome() {
  try {
    const data = await searchItems({ sort: "hot" });
    hotItems.value = data.items || [];
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
  padding: 26px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(16px);
}

.showcase-tabs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
  margin-bottom: 20px;
}
.showcase-tab {
  min-height: 34px;
  padding: 6px 16px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #fff;
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
  text-align: center;
}
.showcase-tab:hover { border-color: rgba(13, 148, 136, 0.35); color: var(--primary-dark); }
.showcase-tab.active {
  border-color: transparent;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #fff;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.22);
}

/* ===== Stats Section ===== */
.intro-stats { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 18px; }
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

/* ===== Responsive ===== */
@media (max-width: 980px) {
  .intro-hero, .intro-stats { grid-template-columns: 1fr; }
  .intro-hero { min-height: auto; padding: 42px; }
  .intro-copy h1 { font-size: 46px; }
  .intro-stage { min-height: 420px; }
  .showcase-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
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
  .intro-stats { grid-template-columns: 1fr; }
  .product-showcase { padding: 18px; }
  .showcase-tabs { gap: 6px; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); }
  .showcase-tab { padding: 5px 10px; font-size: 12px; }
}
</style>
