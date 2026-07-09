<template>
  <div v-if="modelValue" :class="['modal', modalClass]">
    <div :class="['modal-panel', panelClass]">
      <button class="icon-btn modal-close" type="button" aria-label="关闭" @click="$emit('update:modelValue', false)">×</button>
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  modalClass: { type: [String, Array, Object], default: "" },
  panelClass: { type: [String, Array, Object], default: "" },
});
defineEmits(["update:modelValue"]);
</script>
