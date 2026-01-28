<template>
  <div class="sort-chips">
    <button 
      class="neu-sort-chip active"
      @click="onChipClick"
    >
      <span class="chip-icon">{{ currentOption.icon }}</span>
      <span class="chip-label">{{ currentOption.label }}</span>
      <span class="order-icon" @click.stop="toggleOrder">
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

.chip-icon {
  font-size: 14px;
}

.chip-label {
  font-weight: 500;
}
</style>
