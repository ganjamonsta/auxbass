<template>
  <div class="nokia-player" @click="$emit('expand')">
    <!-- Left side buttons - Nokia style -->
    <div class="nokia-side nokia-side-left">
      <button class="nokia-btn nokia-btn-prev" @click.stop="$emit('prev')">
        <span class="nokia-btn-icon">⏮</span>
      </button>
    </div>
    
    <!-- LCD Screen -->
    <div class="lcd-screen">
      <div class="lcd-row lcd-row-main">
        <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
        <div class="lcd-title-container">
          <div class="lcd-title-track" :class="{ 'marquee': shouldMarqueeTitle }">
            <span class="lcd-title">{{ track.title || 'NO TRACK' }}</span>
            <span v-if="shouldMarqueeTitle" class="lcd-title lcd-title-clone">{{ track.title || 'NO TRACK' }}</span>
          </div>
        </div>
      </div>
      <div class="lcd-row lcd-row-sub">
        <div class="lcd-artist-container">
          <div class="lcd-artist-track" :class="{ 'marquee': shouldMarqueeArtist }">
            <span class="lcd-artist">{{ track.artist || '---' }}</span>
            <span v-if="shouldMarqueeArtist" class="lcd-artist lcd-artist-clone">{{ track.artist || '---' }}</span>
          </div>
        </div>
        <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
      </div>
      <!-- LED Progress dots -->
      <div class="lcd-progress">
        <span class="lcd-dot" v-for="i in 16" :key="i" :class="{ active: (i / 16) * 100 <= progressPercent }"></span>
      </div>
    </div>
    
    <!-- Right side buttons - Nokia style -->
    <div class="nokia-side nokia-side-right">
      <button class="nokia-btn nokia-btn-play" :class="{ playing: isPlaying }" @click.stop="$emit('toggle')">
        <svg v-if="loading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M12 2a10 10 0 0 1 10 10"/>
        </svg>
        <span v-else class="nokia-btn-icon">{{ isPlaying ? '⏸' : '▶' }}</span>
      </button>
      <button class="nokia-btn nokia-btn-next" @click.stop="$emit('next')">
        <span class="nokia-btn-icon">⏭</span>
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

const emit = defineEmits(['expand', 'toggle', 'next', 'prev'])

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

const shouldMarqueeArtist = computed(() => {
  return (props.track?.artist?.length || 0) > 15
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* Nokia XpressMusic Style Player */
.nokia-player {
  display: flex;
  align-items: stretch;
  margin: 8px;
  background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 100%);
  border-radius: 12px;
  cursor: pointer;
  z-index: 60;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid #333;
  overflow: hidden;
}

/* Nokia side button panels */
.nokia-side {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  padding: 4px 2px;
  background: linear-gradient(180deg, #d42a2a 0%, #a01515 50%, #8a1010 100%);
  min-width: 28px;
}

.nokia-side-left {
  border-radius: 11px 0 0 11px;
  padding-left: 3px;
}

.nokia-side-right {
  border-radius: 0 11px 11px 0;
  padding-right: 3px;
}

/* Nokia rubber buttons */
.nokia-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 26px;
  border: none;
  background: linear-gradient(180deg, #444 0%, #222 100%);
  border-radius: 4px;
  cursor: pointer;
  color: #ccc;
  font-size: 9px;
  transition: all 0.1s ease;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(0, 0, 0, 0.3);
  /* Rubber texture effect */
  border: 1px solid #1a1a1a;
}

.nokia-btn:active {
  transform: scale(0.92);
  box-shadow: 
    inset 0 2px 4px rgba(0, 0, 0, 0.5);
  background: linear-gradient(180deg, #333 0%, #1a1a1a 100%);
}

.nokia-btn-play {
  height: 30px;
  background: linear-gradient(180deg, #555 0%, #2a2a2a 100%);
}

.nokia-btn-play.playing {
  color: var(--spotify-green);
  text-shadow: 0 0 8px rgba(29, 185, 84, 0.6);
}

.nokia-btn-icon {
  font-size: 10px;
  line-height: 1;
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

.lcd-artist-container {
  flex: 1 1 0;
  min-width: 0;
  overflow: hidden;
  position: relative;
}

.lcd-artist-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-artist-track.marquee {
  animation: marquee-scroll 8s linear infinite;
}

.lcd-artist {
  color: #3399cc;
  font-size: 11px;
  text-shadow: 0 0 4px rgba(51, 153, 204, 0.5);
  white-space: nowrap;
  flex-shrink: 0;
}

.lcd-artist-clone {
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

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
