<script setup>
import { computed } from 'vue'
import TrackItem from './TrackItem.vue'

const props = defineProps({
  artist: { type: Object, default: null },
  tracks: { type: Array, default: () => [] },
  currentTrackId: { type: Number, default: null },
  isPlaying: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'play', 'playAll', 'menu'])

const artistTracks = computed(() => {
  if (!props.artist) return []
  return props.tracks.filter(t => 
    t.artist?.toLowerCase().includes(props.artist.name.toLowerCase())
  )
})

const artistCover = computed(() => {
  const trackWithCover = artistTracks.value.find(t => t.cover_path)
  return trackWithCover?.cover_path || null
})

const totalDuration = computed(() => {
  const total = artistTracks.value.reduce((sum, t) => sum + (t.duration || 0), 0)
  const minutes = Math.floor(total / 60)
  const hours = Math.floor(minutes / 60)
  if (hours > 0) {
    return `${hours}ч ${minutes % 60}м`
  }
  return `${minutes}м`
})
</script>

<template>
  <div v-if="artist" class="artist-view">
    <div class="artist-header">
      <button @click="$emit('close')" class="icon-btn back-btn">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
        </svg>
      </button>
      
      <div class="artist-hero">
        <div class="artist-avatar">
          <img v-if="artistCover" :src="artistCover" alt="">
          <span v-else class="avatar-placeholder">{{ artist.name[0] }}</span>
        </div>
        <h1 class="artist-name">{{ artist.name }}</h1>
        <p class="artist-stats">
          {{ artistTracks.length }} треков • {{ totalDuration }}
        </p>
      </div>
    </div>
    
    <div class="artist-actions">
      <button @click="$emit('playAll')" class="action-btn play-all" :disabled="artistTracks.length === 0">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
      <button class="action-btn shuffle-btn" :disabled="artistTracks.length === 0">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
        </svg>
      </button>
    </div>
    
    <div class="artist-tracks">
      <div v-if="loading" class="loading-spinner">
        <div class="spinner"></div>
      </div>
      <template v-else>
        <TrackItem
          v-for="track in artistTracks"
          :key="track.id"
          :track="track"
          :isPlaying="currentTrackId === track.id && isPlaying"
          :isActive="currentTrackId === track.id"
          @play="$emit('play', track)"
          @menu="$emit('menu', $event)"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.artist-view {
  position: fixed;
  inset: 0;
  background: var(--spotify-black);
  z-index: 60;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.artist-header {
  position: relative;
  padding: 12px;
  background: linear-gradient(180deg, rgba(100, 180, 100, 0.25) 0%, transparent 100%);
  flex-shrink: 0;
}

.back-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
}

.artist-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.artist-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--spotify-gray);
  margin-bottom: 16px;
  box-shadow: 
    8px 8px 20px var(--neu-shadow-dark),
    -4px -4px 12px var(--neu-shadow-light);
}

.artist-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: 600;
  color: var(--spotify-green);
  background: linear-gradient(135deg, var(--spotify-gray) 0%, var(--spotify-gray-dark) 100%);
}

.artist-name {
  font-size: 24px;
  font-weight: 700;
  color: var(--spotify-text);
  text-align: center;
  margin-bottom: 8px;
}

.artist-stats {
  font-size: 13px;
  color: var(--spotify-text-secondary);
}

.artist-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 12px;
  flex-shrink: 0;
}

.action-btn {
  width: 52px;
  height: 52px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  background: var(--neu-bg);
  color: var(--spotify-text);
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -2px -2px 6px var(--neu-shadow-light);
}

.action-btn:disabled {
  opacity: 0.5;
  pointer-events: none;
}

.action-btn.play-all {
  width: 60px;
  height: 60px;
  background: var(--spotify-green);
  color: var(--spotify-black);
}

.action-btn:active {
  transform: scale(0.95);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-dark),
    inset -2px -2px 4px var(--neu-shadow-light);
}

.artist-tracks {
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
  border-top-color: var(--spotify-green);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
