<template>
  <div 
    class="track-item" 
    :class="{ playing: isPlaying, compact: compact }" 
    @click="$emit('click')"
  >
    <!-- Cover with generated gradient -->
    <div class="track-cover" :style="coverStyle">
      <img 
        v-if="track.cover_url" 
        :src="track.cover_url" 
        alt=""
        class="cover-image"
        loading="lazy"
      />
      <span v-else class="cover-text">{{ coverInitials }}</span>
      
      <!-- Playing indicator -->
      <div v-if="isPlaying" class="playing-indicator">
        <div class="bar"></div>
        <div class="bar"></div>
        <div class="bar"></div>
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
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click', 'menu'])

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
  gap: 12px;
  padding: 10px 20px;
  cursor: pointer;
  transition: background 0.2s;
}

.track-item:active {
  background: var(--spotify-gray);
}

.track-item.playing {
  background: rgba(29, 185, 84, 0.1);
}

.track-item.compact {
  padding: 8px 12px;
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.compact .track-cover {
  width: 40px;
  height: 40px;
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
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--spotify-text);
}

.compact .track-title {
  font-size: 14px;
}

.track-item.playing .track-title {
  color: var(--spotify-green);
}

.track-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.track-artist {
  font-size: 13px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact .track-artist {
  font-size: 12px;
}

.play-count {
  font-size: 12px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
}

.track-duration {
  font-size: 13px;
  color: var(--spotify-text-muted);
  flex-shrink: 0;
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
</style>
