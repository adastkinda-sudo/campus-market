<template>
  <section class="page-header animate-in">
    <div><h1>求购市场</h1><p class="muted">认证用户可发布求购需求，卖家可以主动联系。</p></div>
  </section>
  <section v-if="session.canTrade" class="band">
    <form class="form-grid" @submit.prevent="publishWanted">
      <label>求购标题<input v-model="form.title" required /></label>
      <label>分类<select v-model="form.categoryNo"><option value="">不限分类</option><option v-for="category in common.categories" :key="category.categoryNo" :value="category.categoryNo">{{ category.categoryName }}</option></select></label>
      <label>预算<input v-model="form.expectedPrice" type="number" min="0" step="0.01" /></label>
      <label style="grid-column: 1 / -1">求购描述<textarea v-model="form.description" required /></label>
      <button class="btn" type="submit">发布求购</button>
    </form>
  </section>
  <section class="wanted-grid">
    <article v-for="item in wanted" :key="item.wantedNo" class="wanted-card">
      <h3>{{ item.title }}</h3>
      <p>{{ item.description }}</p>
      <div class="meta">
        <span class="pill gold">{{ item.categoryName || "不限分类" }}</span>
        <span class="pill">{{ item.expectedPrice ? money(item.expectedPrice) : "预算面议" }}</span>
        <span class="pill green">{{ item.buyerName }}</span>
      </div>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { createWanted, getWanted } from "../api/modules/wanted.js";
import { useCommonStore } from "../stores/common.js";
import { useSessionStore } from "../stores/session.js";
import { money } from "../utils.js";

const session = useSessionStore();
const common = useCommonStore();

const wanted = ref([]);
const form = reactive({ title: "", categoryNo: "", expectedPrice: "", description: "" });

async function loadWanted() {
  const data = await getWanted();
  wanted.value = data.wanted || [];
}

async function publishWanted() {
  try {
    const data = await createWanted(form);
    session.notify(data.message);
    Object.assign(form, { title: "", categoryNo: "", expectedPrice: "", description: "" });
    await loadWanted();
  } catch (error) {
    session.notify(error.message, true);
  }
}

onMounted(loadWanted);
</script>
