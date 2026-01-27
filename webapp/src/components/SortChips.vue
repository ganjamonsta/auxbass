<template>
  <div class="sort-chips">
    <button 
      class="sort-chip active"
      @click="onChipClick"
    >
      <span class="chip-icon">{{ currentOption.icon }}</span>
      <span class="chip-label">{{ currentOption.label }}</span>
      <span class="chip-order" @click.stop="toggleOrder">
        {{ sortOrder === 'desc' ? '↓' : '↑' }}
      </span>
    </button>
  </div>
</template>

<script setup>
defineProps({
  currentOption: {
    type: Object,
    required: true
  },
  sortOrder: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['next', 'toggle-order'])

const onChipClick = () => {
  emit('next')
}

const toggleOrder = () => {
  emit('toggle-order')
}
</script>

<style scoped>
.sort-chips {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 20px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.sort-chip:active {
  transform: scale(0.95);
}

.sort-chip.active {
  background: var(--accent);
  color: white;
}

.chip-icon {
  font-size: 14px;
}

.chip-label {
  font-weight: 500;
}

.chip-order {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  font-size: 12px;
  margin-left: 2px;
}

.sort-chip:not(.active) .chip-order {
  background: var(--bg-highlight);
}
</style>
