<script setup>
import TrackItem from './TrackItem.vue'

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  currentTrackId: { type: Number, default: null },
  isPlaying: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'play', 'menu', 'clear'])
</script>

<template>
  <div class="history-view">
    <div class="history-header">
      <button @click="$emit('close')" class="icon-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      <h2 class="header-title">История</h2>
      <button v-if="tracks.length > 0" @click="$emit('clear')" class="clear-btn">
        Очистить
      </button>
    </div>
    
    <div class="history-list">
      <div v-if="loading" class="loading-spinner">
        <div class="spinner"></div>
      </div>
      <template v-else>
        <TrackItem
          v-for="track in tracks"
          :key="`${track.id}-${track.played_at}`"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isActive="currentTrackId === track.id"
          @play="$emit('play', track)"
          @menu="$emit('menu', $event)"
        />
        <div v-if="tracks.length === 0" class="empty-state">
          <span class="empty-icon">📜</span>
          <p>История пуста</p>
          <span class="empty-hint">Прослушанные треки появятся здесь</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.history-view {
  position: fixed;
  inset: 0;
  background: var(--spotify-black);
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(100, 100, 180, 0.2), rgba(80, 80, 150, 0.15));
  flex-shrink: 0;
}

.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 600;
  color: var(--spotify-text);
}

.clear-btn {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  background: transparent;
  color: var(--spotify-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:active {
  background: rgba(255, 100, 100, 0.2);
  border-color: #ff6b6b;
  color: #ff6b6b;
}

.history-list {
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
  border-top-color: #6b7aff;
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
