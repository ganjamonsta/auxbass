<template>
  <div 
    class="track-item" 
    :class="{ playing: isPlaying, compact: compact, unavailable: track.is_unavailable }" 
    @click="handleClick"
  >
    <!-- Cover with generated gradient -->
    <div class="track-cover" :style="coverStyle">
      <img 
        v-if="track.cover_url && !track.is_unavailable" 
        :src="track.cover_url" 
        alt=""
        class="cover-image"
        loading="lazy"
      />
      <span v-else class="cover-text">{{ track.is_unavailable ? '✕' : coverInitials }}</span>
      
      <!-- Playing indicator -->
      <div v-if="isPlaying" class="playing-indicator">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
      </div>
      
      <!-- Unavailable overlay -->
      <div v-if="track.is_unavailable" class="unavailable-overlay">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
      </div>
    </div>
    
    <div class="track-info">
      <div class="track-title">{{ track.title || 'Без названия' }}</div>
      <div class="track-meta">
        <span class="track-artist">{{ track.artist || 'Неизвестный' }}</span>
        <span v-if="track.play_count" class="play-count">• {{ track.play_count }} прослушиваний</span>
      </div>
    </div>
    
    <div class="track-duration">
      {{ formatDuration(track.duration) }}
    </div>
    
    <button 
      class="track-like" 
      :class="{ liked: isLiked }" 
      @click.stop="$emit('like')"
    >
      <svg v-if="isLiked" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
      </svg>
    </button>
    
    <button v-if="!compact" class="track-menu" @click.stop="$emit('menu')">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
      </svg>
    </button>
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
  isLiked: {
    type: Boolean,
    default: false
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'menu', 'like'])

const handleClick = () => {
  if (props.track.is_unavailable) {
    // Don't play unavailable tracks, just emit for potential action
    emit('menu')
    return
  }
  emit('click')
}

// Generate cover gradient from title
const coverGradient = computed(() => {
  const title = props.track?.title || 'Music'
  const artist = props.track?.artist || ''
  
  const str = title + artist
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return `linear-gradient(135deg, hsl(${hue1}, 60%, 40%) 0%, hsl(${hue2}, 50%, 30%) 100%)`
})

const coverStyle = computed(() => {
  if (props.track?.cover_url) return {}
  return { background: coverGradient.value }
})

const coverInitials = computed(() => {
  const title = props.track?.title || 'M'
  const words = title.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.substring(0, 2).toUpperCase()
})

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
  gap: 8px;
  padding: 6px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.track-item:active {
  background: var(--spotify-gray);
}

.track-item.playing {
  background: rgba(29, 185, 84, 0.1);
}

.track-item.compact {
  padding: 5px 10px;
}

.track-cover {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -1px -1px 3px var(--neu-shadow-light);
}

.compact .track-cover {
  width: 38px;
  height: 38px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.compact .cover-text {
  font-size: 14px;
}

/* Playing indicator (equalizer animation) */
.playing-indicator {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  padding-bottom: 12px;
}

.playing-indicator .bar {
  width: 3px;
  background: var(--spotify-green);
  border-radius: 1px;
  animation: equalizer 0.8s ease-in-out infinite;
}

.playing-indicator .bar:nth-child(1) {
  height: 8px;
  animation-delay: 0s;
}

.playing-indicator .bar:nth-child(2) {
  height: 16px;
  animation-delay: 0.2s;
}

.playing-indicator .bar:nth-child(3) {
  height: 12px;
  animation-delay: 0.4s;
}

@keyframes equalizer {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(0.5); }
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--spotify-text);
}

.compact .track-title {
  font-size: 12px;
}

.track-item.playing .track-title {
  color: var(--spotify-green);
}

.track-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 1px;
}

.track-artist {
  font-size: 11px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact .track-artist {
  font-size: 10px;
}

.play-count {
  font-size: 10px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
}

.track-duration {
  font-size: 11px;
  color: var(--spotify-text-muted);
  flex-shrink: 0;
}

.track-like {
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-muted);
  cursor: pointer;
  opacity: 0.6;
  transition: all 0.2s;
  flex-shrink: 0;
}

.track-like:hover,
.track-like:active {
  opacity: 1;
}

.track-like.liked {
  color: #1db954;
  opacity: 1;
}

.track-menu {
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-muted);
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.track-menu:active {
  opacity: 1;
}

/* Unavailable track styles */
.track-item.unavailable {
  opacity: 0.5;
}

.track-item.unavailable .track-title {
  text-decoration: line-through;
  color: var(--spotify-text-muted);
}

.track-item.unavailable .track-cover {
  filter: grayscale(100%);
}

.unavailable-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
}
</style>
