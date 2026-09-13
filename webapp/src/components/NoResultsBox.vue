<template>
  <div class="no-results-box">
    <p class="no-results-text">{{ text }}</p>
    <p v-if="hint" class="no-results-hint">{{ hint }}</p>
    <slot></slot>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    required: true
  },
  hint: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.no-results-box {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.no-results-text {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: var(--c-text-1, #fff);
}

.no-results-hint {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
  margin: 0;
  line-height: 1.4;
}
</style>
