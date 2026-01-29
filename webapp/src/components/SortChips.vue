<template>
  <div class="sort-chips">
    <button 
      class="neu-sort-chip active"
      @click="onChipClick"
    >
      <component :is="iconComponent" :size="14" class="chip-icon" />
      <span class="chip-label">{{ currentOption.label }}</span>
      <span class="order-icon" @click.stop="toggleOrder">
        <ArrowDown v-if="sortOrder === 'desc'" :size="14" />
        <ArrowUp v-else :size="14" />
      </span>
    </button>
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

const iconComponent = computed(() => iconMap[props.currentOption.icon] || Music)

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
