<template>
  <div class="playlist-item" @click="$emit('click')">
    <div class="playlist-cover">
      📁
    </div>
    
    <div class="playlist-info">
      <div class="playlist-name">{{ playlist.name }}</div>
      <div class="playlist-meta">
        {{ playlist.track_count }} треков • {{ formatDuration(playlist.total_duration) }}
      </div>
    </div>
    
    <div class="playlist-arrow">›</div>
  </div>
</template>

<script setup>
const props = defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const formatDuration = (seconds) => {
  if (!seconds) return '0 мин'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours} ч ${minutes} мин`
  return `${minutes} мин`
}
</script>

<style scoped>
.playlist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--tg-theme-secondary-bg-color);
}

.playlist-item:active {
  background: var(--tg-theme-secondary-bg-color);
}

.playlist-cover {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 2px;
}

.playlist-meta {
  font-size: 13px;
  color: var(--tg-theme-hint-color);
}

.playlist-arrow {
  font-size: 24px;
  color: var(--tg-theme-hint-color);
}
</style>
