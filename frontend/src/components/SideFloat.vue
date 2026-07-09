<template>
  <div class="side-float">
    <RouterLink class="float-btn" to="/contact" title="联系客服">
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
import { RouterLink } from "vue-router";

const showTop = ref(false);

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
