<template>
  <div class="upload-box">
    <span class="upload-label">{{ label }}</span>
    <div class="upload-row">
      <label class="upload-btn">
        选择文件
        <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" @change="onChange" />
      </label>
      <span class="upload-status">{{ statusText }}</span>
    </div>
    <small v-if="hint" class="upload-hint">{{ hint }}</small>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { uploadImage } from "../api/modules/uploads.js";
import { useSessionStore } from "../stores/session.js";

const props = defineProps({
  modelValue: String,
  purpose: { type: String, default: "item" },
  label: { type: String, default: "上传图片" },
  hint: String,
});
const emit = defineEmits(["update:modelValue"]);
const loading = ref(false);
const session = useSessionStore();

const statusText = computed(() => {
  if (loading.value) return "上传中...";
  if (props.modelValue) return "已上传";
  return "未选择文件";
});

async function onChange(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  loading.value = true;
  try {
    const data = await uploadImage(file, props.purpose);
    emit("update:modelValue", data.url);
    session.notify(data.message);
  } catch (error) {
    session.notify(error.message, true);
  } finally {
    loading.value = false;
    event.target.value = "";
  }
}
</script>

<style scoped>
.upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.upload-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 4px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: all 0.16s ease;
  white-space: nowrap;
}
.upload-btn:hover { border-color: var(--primary); color: var(--primary); }
.upload-btn input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.upload-status { color: var(--muted); font-size: 13px; }
.upload-hint { color: var(--muted); }
</style>
