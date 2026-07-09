<template>
  <section v-if="!isUser()" class="empty-state animate-in">
    <span class="icon">🔒</span>
    <strong>需要先登录</strong>
    <p>登录用户账号后才能发布闲置物品。</p>
    <RouterLink class="btn" to="/account">去登录</RouterLink>
  </section>

  <template v-else>
    <section class="page-header animate-in">
      <div>
        <h1>发布管理</h1>
        <p class="muted">认证用户且信用积分不低于 60 才能发布闲置。</p>
      </div>
      <span :class="['pill', canTrade() ? 'green' : 'gold']">{{ canTrade() ? "可发布" : "受限" }}</span>
    </section>

    <section class="split">
      <div class="band animate-in delay-1">
        <div class="section-head"><h2>发布闲置物品</h2></div>
        <form v-if="canTrade()" class="form-grid" @submit.prevent="publishItem">
          <label>物品标题<input v-model="form.title" required /></label>
          <label>分类
            <select v-model="form.categoryNo" required>
              <option v-for="category in state.categories" :key="category.categoryNo" :value="category.categoryNo">{{ category.categoryName }}</option>
            </select>
          </label>
          <label>校区
            <select v-model="form.campusName" required><option>徐汇校区</option><option>奉贤校区</option></select>
          </label>
          <label>原价<input v-model="form.originalPrice" type="number" min="0" step="0.01" required /></label>
          <label>二手价<input v-model="form.sellPrice" type="number" min="0" step="0.01" required /></label>
          <label>新旧程度
            <select v-model="form.condition"><option>全新</option><option>九成新</option><option>八成新</option><option>七成新</option><option>使用痕迹明显</option></select>
          </label>
          <FileUpload v-model="form.imageUrl" purpose="item" label="商品图片" />
          <label style="grid-column: 1 / -1">详细描述<textarea v-model="form.description" required /></label>
          <button class="btn" type="submit">发布物品</button>
        </form>
        <div v-else class="empty-state">
          <span class="icon">🛡️</span>
          <strong>发布受限</strong>
          <p>请先完成校园认证，或等待信用积分恢复到 60 以上。</p>
        </div>
      </div>

      <div class="band animate-in delay-2">
        <div class="section-head"><h2>我的发布</h2></div>
        <div v-if="myItems.length" class="manage-grid">
          <ProductCard
            v-for="item in myItems"
            :key="item.itemNo"
            :item="item"
            compact
            editable
            @detail="openDetail"
            @edit="openEdit"
            @shelve="shelveItem"
          />
        </div>
        <div v-else class="empty">暂无发布</div>
      </div>
    </section>
  </template>

  <ItemDetailModal v-model="detailOpen" :item-no="activeItemNo" @changed="loadMyItems" />
  <BaseModal v-model="editOpen">
    <section v-if="editForm.itemNo" class="band slim">
      <div class="section-head"><h2>编辑物品</h2></div>
      <form class="form-grid" @submit.prevent="saveEdit">
        <label>物品标题<input v-model="editForm.title" required /></label>
        <label>分类
          <select v-model="editForm.categoryNo" required>
            <option v-for="category in state.categories" :key="category.categoryNo" :value="category.categoryNo">{{ category.categoryName }}</option>
          </select>
        </label>
        <label>校区<select v-model="editForm.campusName" required><option>徐汇校区</option><option>奉贤校区</option></select></label>
        <label>原价<input v-model="editForm.originalPrice" type="number" min="0" step="0.01" required /></label>
        <label>二手价<input v-model="editForm.sellPrice" type="number" min="0" step="0.01" required /></label>
        <label>新旧程度<select v-model="editForm.condition"><option>全新</option><option>九成新</option><option>八成新</option><option>七成新</option><option>使用痕迹明显</option></select></label>
        <FileUpload v-model="editForm.imageUrl" purpose="item" label="商品图片" />
        <label style="grid-column: 1 / -1">详细描述<textarea v-model="editForm.description" required /></label>
        <button class="btn" type="submit">保存修改</button>
      </form>
    </section>
  </BaseModal>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../api/client.js";
import BaseModal from "../components/BaseModal.vue";
import FileUpload from "../components/FileUpload.vue";
import ItemDetailModal from "../components/ItemDetailModal.vue";
import ProductCard from "../components/ProductCard.vue";
import { canTrade, isUser, loadCommon, notify, state } from "../state/session.js";

const blankForm = () => ({ title: "", categoryNo: "", campusName: "奉贤校区", originalPrice: "", sellPrice: "", condition: "八成新", imageUrl: "", description: "" });
const form = reactive(blankForm());
const editForm = reactive({ ...blankForm(), itemNo: null });
const myItems = ref([]);
const detailOpen = ref(false);
const editOpen = ref(false);
const activeItemNo = ref(null);

function resetForm() {
  Object.assign(form, blankForm(), { categoryNo: state.categories[0]?.categoryNo || "" });
}

function openDetail(item) {
  activeItemNo.value = item.itemNo;
  detailOpen.value = true;
}

async function loadMyItems() {
  if (!isUser()) return;
  const data = await api("/api/items?status=全部&sort=new");
  myItems.value = (data.items || []).filter((item) => item.sellerNo === state.principal.userNo);
}

async function publishItem() {
  try {
    const data = await api("/api/items", { method: "POST", body: JSON.stringify(form) });
    notify(data.message);
    resetForm();
    await loadCommon();
    await loadMyItems();
  } catch (error) {
    notify(error.message, true);
  }
}

async function openEdit(item) {
  try {
    const data = await api(`/api/items/${item.itemNo}`);
    Object.assign(editForm, data.item);
    editOpen.value = true;
  } catch (error) {
    notify(error.message, true);
  }
}

async function saveEdit() {
  try {
    const data = await api(`/api/items/${editForm.itemNo}`, { method: "PUT", body: JSON.stringify(editForm) });
    notify(data.message);
    editOpen.value = false;
    await loadMyItems();
  } catch (error) {
    notify(error.message, true);
  }
}

async function shelveItem(item) {
  if (!window.confirm(`确定下架「${item.title}」吗？下架后它会从我的发布和市场中隐藏。`)) return;
  try {
    const data = await api(`/api/items/${item.itemNo}/status`, { method: "POST", body: JSON.stringify({ status: "已下架" }) });
    notify(data.message);
    await loadCommon();
    await loadMyItems();
  } catch (error) {
    notify(error.message, true);
  }
}

onMounted(async () => {
  resetForm();
  await loadMyItems();
});
</script>
