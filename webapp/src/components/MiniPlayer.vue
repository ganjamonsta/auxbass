<template>
  <div class="mini-player" @click="$emit('expand')">
    <!-- LCD Screen -->
    <div class="lcd-screen">
      <div class="lcd-row lcd-row-main">
        <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
        <span class="lcd-title">{{ displayTitle }}</span>
      </div>
      <div class="lcd-row lcd-row-sub">
        <div class="lcd-artist-container">
          <span class="lcd-artist" :class="{ 'marquee': shouldMarqueeArtist }">{{ track.artist || '---' }}</span>
        </div>
        <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
      </div>
      <!-- LED Progress dots -->
      <div class="lcd-progress">
        <span class="lcd-dot" v-for="i in 16" :key="i" :class="{ active: (i / 16) * 100 <= progressPercent }"></span>
      </div>
    </div>
    
    <!-- Controls -->
    <button class="ctrl-btn" @click.stop="$emit('toggle')">
      <svg v-if="loading" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
        <path d="M12 2a10 10 0 0 1 10 10"/>
      </svg>
      <template v-else>{{ isPlaying ? '❚❚' : '▶' }}</template>
    </button>
    <button class="ctrl-btn" @click.stop="$emit('next')">▶▶</button>
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
  loading: {
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
  },
  buffered: {
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

const bufferedPercent = computed(() => {
  const dur = props.duration || props.track?.duration
  if (!dur) return 0
  return (props.buffered / dur) * 100
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

const shouldMarquee = computed(() => {
  return (props.track?.title?.length || 0) > 18
})

const shouldMarqueeArtist = computed(() => {
  return (props.track?.artist?.length || 0) > 20
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const displayTitle = computed(() => {
  const title = props.track?.title || 'NO TRACK'
  return title.length > 22 ? title.substring(0, 20) + '..' : title
})
</script>

<style scoped>
/* Neumorphism Mini Player with LCD Screen */
.mini-player {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 12px 8px;
  padding: 8px 10px;
  background: var(--neu-bg);
  border-radius: 16px;
  cursor: pointer;
  z-index: 60;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark),
    -3px -3px 8px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

/* LCD Screen - Car Stereo Style */
.lcd-screen {
  flex: 1;
  background: linear-gradient(180deg, #0a1525 0%, #061020 100%);
  border-radius: 8px;
  padding: 8px 12px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  border: 1px solid #1a2a40;
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.8),
    0 1px 0 rgba(100, 150, 255, 0.1);
  min-width: 0;
}

.lcd-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.lcd-row-main {
  margin-bottom: 2px;
}

.lcd-row-sub {
  justify-content: space-between;
  margin-bottom: 6px;
}

.lcd-status {
  color: #00aaff;
  font-size: 11px;
  text-shadow: 0 0 6px rgba(0, 170, 255, 0.8);
  flex-shrink: 0;
}

.lcd-title {
  color: #4dc3ff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
}

.lcd-artist-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  position: relative;
  mask-image: linear-gradient(90deg, transparent, black 4px, black calc(100% - 8px), transparent);
  -webkit-mask-image: linear-gradient(90deg, transparent, black 4px, black calc(100% - 8px), transparent);
}

.lcd-artist {
  display: inline-block;
  color: #3399cc;
  font-size: 11px;
  text-shadow: 0 0 4px rgba(51, 153, 204, 0.5);
  white-space: nowrap;
  padding-left: 4px;
}

.lcd-artist.marquee {
  animation: marquee-artist 8s linear infinite;
}

@keyframes marquee-artist {
  0% {
    transform: translateX(0%);
  }
  10% {
    transform: translateX(0%);
  }
  45% {
    transform: translateX(calc(-100% + 100px));
  }
  55% {
    transform: translateX(calc(-100% + 100px));
  }
  90% {
    transform: translateX(0%);
  }
  100% {
    transform: translateX(0%);
  }
}

.lcd-time {
  color: #66ccff;
  font-size: 11px;
  font-weight: 500;
  text-shadow: 0 0 4px rgba(102, 204, 255, 0.5);
  flex-shrink: 0;
  letter-spacing: 1px;
}

/* Progress dots */
.lcd-progress {
  display: flex;
  gap: 3px;
}

.lcd-dot {
  width: 100%;
  height: 3px;
  background: #0a2035;
  border-radius: 1px;
  flex: 1;
}

.lcd-dot.active {
  background: #00ccff;
  box-shadow: 0 0 4px rgba(0, 204, 255, 0.8);
}

/* Neumorphic Control Buttons */
.ctrl-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--neu-bg);
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-muted);
  font-size: 10px;
  flex-shrink: 0;
  transition: all 0.15s ease;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 5px var(--neu-shadow-light);
}

.ctrl-btn:active {
  transform: scale(0.95);
  box-shadow: 
    inset 2px 2px 5px var(--neu-shadow-dark),
    inset -1px -1px 3px var(--neu-shadow-light);
  color: var(--spotify-green);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
