<template>
  <div class="mini-player" @click="$emit('expand')">
    <!-- LCD Screen -->
    <div class="lcd-screen">
      <div class="lcd-row lcd-row-main">
        <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
        <div class="lcd-title-container">
          <div class="lcd-title-track" :class="{ 'marquee': shouldMarquee }">
            <span class="lcd-title">{{ displayText }}</span>
            <span v-if="shouldMarquee" class="lcd-title lcd-title-clone">{{ displayText }}</span>
          </div>
        </div>
      </div>
      <div class="lcd-row lcd-row-sub">
        <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
      </div>
      <!-- LED Progress dots -->
      <div class="lcd-progress">
        <span class="lcd-dot" v-for="i in 16" :key="i" :class="{ active: (i / 16) * 100 <= progressPercent }"></span>
      </div>
    </div>
    
    <!-- Nokia Style Controls -->
    <div class="nokia-controls">
      <button class="nokia-btn" @click.stop="$emit('toggle')">
        <svg v-if="loading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M12 2a10 10 0 0 1 10 10"/>
        </svg>
        <svg v-else-if="isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16" rx="1"/>
          <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
      <button class="nokia-btn" @click.stop="$emit('next')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 18l8.5-6L6 6v12zm8-12v12l8-6-8-6z"/>
        </svg>
      </button>
    </div>
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

const shouldMarqueeTitle = computed(() => {
  return (props.track?.title?.length || 0) > 20
})

const displayText = computed(() => {
  const artist = props.track?.artist || '---'
  const title = props.track?.title || 'NO TRACK'
  return `${artist} — ${title}`
})

const shouldMarquee = computed(() => {
  return displayText.value.length > 25
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
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
  min-width: 0;
}

.lcd-row-main {
  margin-bottom: 2px;
  min-width: 0;
}

.lcd-row-sub {
  justify-content: space-between;
  margin-bottom: 6px;
  min-width: 0;
  overflow: hidden;
}

.lcd-status {
  color: #00aaff;
  font-size: 11px;
  text-shadow: 0 0 6px rgba(0, 170, 255, 0.8);
  flex-shrink: 0;
}

.lcd-title-container {
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
  position: relative;
}

.lcd-title-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-title-track.marquee {
  animation: marquee-scroll 8s linear infinite;
}

.lcd-title {
  color: #4dc3ff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  white-space: nowrap;
  flex-shrink: 0;
}

.lcd-title-clone {
  margin-left: 60px;
}

@keyframes marquee-scroll {
  0%, 10% {
    transform: translateX(0);
  }
  90%, 100% {
    transform: translateX(calc(-50% - 30px));
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

/* Nokia XpressMusic Style Controls */
.nokia-controls {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.nokia-btn {
  width: 38px;
  height: 28px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  transition: all 0.15s ease;
  position: relative;
  
  /* Nokia rubber button style */
  background: linear-gradient(180deg, 
    #3a3a3a 0%, 
    #252525 50%, 
    #1a1a1a 100%);
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  border: 1px solid #0a0a0a;
}

/* Rubber texture bumps */
.nokia-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 14px;
  background: 
    radial-gradient(circle at 20% 50%, rgba(255,255,255,0.08) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(255,255,255,0.08) 0%, transparent 40%),
    radial-gradient(circle at 80% 50%, rgba(255,255,255,0.08) 0%, transparent 40%);
  border-radius: 3px;
  pointer-events: none;
}

.nokia-btn:active {
  transform: scale(0.96);
  background: linear-gradient(180deg, 
    #2a2a2a 0%, 
    #1a1a1a 50%, 
    #151515 100%);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.nokia-btn:active svg {
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
