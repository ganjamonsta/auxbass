<template>
  <div class="sort-chips">
    <div class="sort-buttons">
      <button 
        class="sort-btn mode-btn"
        @click="onChipClick"
      >
        <component :is="iconComponent" :size="16" class="chip-icon" />
      </button>
      <button 
        class="sort-btn order-btn"
        @click="toggleOrder"
      >
        <ArrowDown v-if="sortOrder === 'desc'" :size="16" />
        <ArrowUp v-else :size="16" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Calendar, Type, User, Clock, Music, Disc3, ArrowUp, ArrowDown } from 'lucide-vue-next'

const iconMap = {
  Calendar,
  Type,
  User,
  Clock,
  Music,
  Disc3
}

const props = defineProps({
  currentOption: {
    type: Object,
    required: true
  },
  sortOrder: {
    type: String,
    required: true
  }
})

const iconComponent = computed(() => {
  // Support both 'icon' field from options (useSort uses this)
  // and fallback to Music if not provided
  return iconMap[props.currentOption.icon] || Music
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

.sort-buttons {
  display: flex;
  border-radius: 28px;
  background: var(--c-accent);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -3px -3px 8px rgba(255, 255, 255, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.sort-btn {
  height: 40px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #000;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  font-size: 13px;
  font-weight: 500;
}

.sort-btn:active {
  background: rgba(0, 0, 0, 0.1);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.15);
}

.mode-btn {
  width: 40px;
  padding: 0;
}

.mode-btn::after {
  content: '';
  position: absolute;
  top: 10px;
  bottom: 10px;
  right: 0;
  width: 1px;
  background: rgba(0, 0, 0, 0.15);
}

.order-btn {
  width: 40px;
  padding: 0;
}

.chip-icon {
  flex-shrink: 0;
}
</style>
