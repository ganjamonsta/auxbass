<template>
  <header class="page-header">
    <button v-if="showBack" class="back-btn" @click="$emit('goBack')">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
      </svg>
    </button>
    <h1 class="page-title">{{ title }}</h1>
    <div v-if="$slots.toggle" class="header-toggle">
      <slot name="toggle"></slot>
    </div>
    <div class="header-actions">
      <slot name="actions"></slot>
    </div>
  </header>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  showBack: {
    type: Boolean,
    default: true
  }
})

defineEmits(['goBack'])
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-primary);
  position: sticky;
  top: 0;
  z-index: 50;
}

.back-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.back-btn:hover {
  background: var(--bg-elevated);
}

.page-title {
  flex: 1;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-toggle {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 3px;
}

.header-toggle :deep(.toggle-btn) {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-toggle :deep(.toggle-btn.active) {
  background: var(--accent-color, #1db954);
  color: #fff;
}
</style>
