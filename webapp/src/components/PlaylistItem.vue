<template>
  <div class="playlist-item" @click="$emit('click')">
    <div class="playlist-cover" :class="{ 'has-image': playlist.cover_url }">
      <img v-if="playlist.cover_url" :src="playlist.cover_url" alt="" class="cover-image" />
      <span v-else class="cover-icon">{{ coverIcon }}</span>
    </div>
    
    <div class="playlist-info">
      <div class="playlist-name">{{ playlist.name }}</div>
      <div class="playlist-meta">
        <span v-if="playlist.is_auto_source" class="meta-badge source">{{ sourceLabel }}</span>
        <span v-else-if="playlist.is_auto_album" class="meta-badge album">Альбом</span>
        {{ playlist.track_count }} треков • {{ formatDuration(playlist.total_duration) }}
      </div>
    </div>
    
    <div class="playlist-arrow">›</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  playlist: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const coverIcon = computed(() => {
  if (props.playlist.is_auto_source) {
    const type = props.playlist.source_type
    if (type === 'bot') return '🤖'
    if (type === 'channel') return '📢'
    if (type === 'user') return '👤'
    return '📁'
  }
  if (props.playlist.is_auto_album) return '💿'
  return '📁'
})

const sourceLabel = computed(() => {
  const type = props.playlist.source_type
  if (type === 'bot') return 'Бот'
  if (type === 'channel') return 'Канал'
  if (type === 'user') return 'Пользователь'
  return 'Источник'
})

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
  padding: 10px 12px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s;
}

.playlist-item:active {
  background: var(--tg-theme-secondary-bg-color);
}

.playlist-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.playlist-cover.has-image {
  background: transparent;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-icon {
  font-size: 22px;
}

.playlist-info {
  flex: 1;
  min-width: 0;
}

.playlist-name {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-meta {
  font-size: 12px;
  color: var(--tg-theme-hint-color);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.meta-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  text-transform: uppercase;
}

.meta-badge.source {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.meta-badge.album {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.playlist-arrow {
  font-size: 20px;
  color: var(--tg-theme-hint-color);
  opacity: 0.5;
}
</style>
