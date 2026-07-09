<template>
  <label class="upload-box">
    <span>{{ label }}</span>
    <input type="file" accept="image/png,image/jpeg,image/webp,image/gif" @change="onChange" />
    <strong v-if="loading">上传中...</strong>
    <strong v-else-if="modelValue">已上传</strong>
    <small v-if="hint">{{ hint }}</small>
  </label>
</template>

<script setup>
import { ref } from "vue";
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
