<template>
  <div class="mini-player" @click="$emit('expand')">
    <div class="mini-cover">
      🎵
    </div>
    
    <div class="mini-info">
      <div class="mini-title">{{ track.title || 'Без названия' }}</div>
      <div class="mini-artist">{{ track.artist || 'Неизвестный исполнитель' }}</div>
    </div>
    
    <button class="mini-btn" @click.stop="$emit('toggle')">
      <span v-if="isPlaying">⏸</span>
      <span v-else>▶</span>
    </button>
    
    <button class="mini-btn" @click.stop="$emit('next')">
      ⏭
    </button>
    
    <!-- Progress bar -->
    <div class="mini-progress">
      <div class="mini-progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  isPlaying: {
    type: Boolean,
    default: false
  },
  progress: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['expand', 'toggle', 'next'])

const progressPercent = computed(() => {
  if (!props.track.duration) return 0
  return (props.progress / props.track.duration) * 100
})
</script>

<style scoped>
.mini-player {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--tg-theme-bg-color);
  border-top: 1px solid var(--tg-theme-secondary-bg-color);
  cursor: pointer;
  z-index: 50;
}

.mini-cover {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.mini-info {
  flex: 1;
  min-width: 0;
}

.mini-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-artist {
  font-size: 12px;
  color: var(--tg-theme-hint-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-progress {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--tg-theme-secondary-bg-color);
}

.mini-progress-fill {
  height: 100%;
  background: var(--tg-theme-button-color);
  transition: width 0.1s linear;
}
</style>
