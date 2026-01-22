<template>
  <div class="mini-player" @click="$emit('expand')">
    <!-- Progress bar at top -->
    <div class="mini-progress">
      <div class="mini-progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>
    
    <!-- Cover -->
    <div class="mini-cover" :style="coverStyle">
      <img 
        v-if="track.cover_url" 
        :src="track.cover_url" 
        alt=""
        class="cover-image"
      />
      <span v-else class="cover-text">{{ coverInitials }}</span>
    </div>
    
    <!-- Info -->
    <div class="mini-info">
      <div class="mini-title">{{ track.title || 'Без названия' }}</div>
      <div class="mini-artist">{{ track.artist || 'Неизвестный' }}</div>
    </div>
    
    <!-- Controls -->
    <button class="mini-btn" @click.stop="$emit('toggle')">
      <svg v-if="isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
      </svg>
      <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M8 5v14l11-7z"/>
      </svg>
    </button>
    
    <button class="mini-btn" @click.stop="$emit('next')">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
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
  progress: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['expand', 'toggle', 'next'])

const progressPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return (props.progress / dur) * 100
})

// Generate cover gradient
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
</script>

<style scoped>
.mini-player {
  position: fixed;
  bottom: 64px; /* Above tab bar */
  left: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--spotify-gray);
  border-radius: 8px;
  cursor: pointer;
  z-index: 60;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.mini-progress {
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 2px;
  background: var(--spotify-gray-dark);
  border-radius: 1px;
}

.mini-progress-fill {
  height: 100%;
  background: var(--spotify-green);
  border-radius: 1px;
  transition: width 0.2s linear;
}

.mini-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
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

.mini-info {
  flex: 1;
  min-width: 0;
}

.mini-title {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--spotify-text);
}

.mini-artist {
  font-size: 12px;
  color: var(--spotify-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.mini-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text);
  flex-shrink: 0;
  transition: transform 0.1s;
}

.mini-btn:active {
  transform: scale(0.95);
}
</style>
