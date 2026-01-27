<script setup>
import { computed } from 'vue'
import TrackItem from './TrackItem.vue'

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  currentTrackId: { type: Number, default: null },
  isPlaying: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'play', 'playAll', 'menu', 'scrollToLast'])

const sortedTracks = computed(() => {
  return [...props.tracks].sort((a, b) => {
    const dateA = new Date(a.liked_at || 0)
    const dateB = new Date(b.liked_at || 0)
    return dateB - dateA
  })
})
</script>

<template>
  <div class="liked-view">
    <div class="liked-header">
      <button @click="$emit('close')" class="icon-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <h2 class="header-title">Понравившиеся</h2>
      <span class="track-count">{{ tracks.length }}</span>
    </div>
    
    <div class="liked-actions">
      <button @click="$emit('playAll')" class="action-btn play-all" :disabled="tracks.length === 0">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
        Воспроизвести
      </button>
      <button @click="$emit('scrollToLast')" class="action-btn" :disabled="tracks.length === 0">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.59 8.59L12 13.17 7.41 8.59 6 10l6 6 6-6z"/>
        </svg>
        К последнему
      </button>
    </div>
    
    <div class="liked-list" ref="listRef">
      <div v-if="loading" class="loading-spinner">
        <div class="spinner"></div>
      </div>
      <template v-else>
        <TrackItem
          v-for="track in sortedTracks"
          :key="track.id"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isActive="currentTrackId === track.id"
          @play="$emit('play', track)"
          @menu="$emit('menu', $event)"
        />
        <div v-if="tracks.length === 0" class="empty-state">
          <span class="empty-icon">❤️</span>
          <p>Нет понравившихся треков</p>
          <span class="empty-hint">Нажмите ♡ на треке, чтобы добавить</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.liked-view {
  position: fixed;
  inset: 0;
  background: var(--spotify-black);
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.liked-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(255, 70, 100, 0.2), rgba(200, 50, 80, 0.15));
  flex-shrink: 0;
}

.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: var(--spotify-text);
}

.track-count {
  padding: 4px 10px;
  background: rgba(255, 70, 100, 0.3);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: #ff6b8a;
}

.liked-actions {
  display: flex;
  gap: 10px;
  padding: 12px;
  flex-shrink: 0;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border: none;
  border-radius: 8px;
  background: var(--spotify-gray);
  color: var(--spotify-text);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:disabled {
  opacity: 0.5;
  pointer-events: none;
}

.action-btn.play-all {
  background: linear-gradient(135deg, #ff4564, #c8325a);
  color: white;
}

.action-btn:active {
  transform: scale(0.97);
}

.liked-list {
  flex: 1;
  overflow-y: overlay;
  scrollbar-gutter: auto;
  padding-bottom: 140px;
}

.icon-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: var(--neu-bg);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  transition: all 0.2s ease;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 6px var(--neu-shadow-light);
}

.icon-btn:active {
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-dark),
    inset -2px -2px 4px var(--neu-shadow-light);
  transform: scale(0.95);
}

.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--spotify-gray-light);
  border-top-color: #ff4564;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--spotify-text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 12px;
  opacity: 0.6;
}
</style>
