<template>
  <div class="track-item" :class="{ playing: isPlaying }" @click="$emit('click')">
    <div class="track-cover" :class="{ 'has-image': track.cover_url }">
      <img 
        v-if="track.cover_url" 
        :src="track.cover_url" 
        alt=""
        class="cover-image"
        loading="lazy"
      />
      <span v-else-if="!isPlaying">🎵</span>
      <span v-else class="playing-icon">▶</span>
      <!-- Playing overlay on cover -->
      <div v-if="track.cover_url && isPlaying" class="playing-overlay">▶</div>
    </div>
    
    <div class="track-info">
      <div class="track-title">{{ track.title || 'Без названия' }}</div>
      <div class="track-artist">{{ track.artist || 'Неизвестный исполнитель' }}</div>
    </div>
    
    <div class="track-duration">
      {{ formatDuration(track.duration) }}
    </div>
    
    <button class="track-menu" @click.stop="$emit('menu')">
      ⋮
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  isPlaying: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'menu'])

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.track-item:active {
  background: var(--tg-theme-secondary-bg-color);
}

.track-item.playing {
  background: var(--tg-theme-secondary-bg-color);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: var(--tg-theme-secondary-bg-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.playing-icon {
  color: var(--tg-theme-button-color);
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-item.playing .track-title {
  color: var(--tg-theme-button-color);
}

.track-artist {
  font-size: 13px;
  color: var(--tg-theme-hint-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-duration {
  font-size: 13px;
  color: var(--tg-theme-hint-color);
  flex-shrink: 0;
}

.track-menu {
  background: none;
  border: none;
  font-size: 20px;
  color: var(--tg-theme-hint-color);
  padding: 8px;
  cursor: pointer;
}

.track-cover.has-image {
  position: relative;
  overflow: hidden;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.playing-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  border-radius: 6px;
}
</style>
