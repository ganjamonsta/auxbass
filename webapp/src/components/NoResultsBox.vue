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
