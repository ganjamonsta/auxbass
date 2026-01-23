<template>
  <div class="mini-player" @click="$emit('expand')">
    <!-- LCD Screen Frame -->
    <div class="lcd-frame">
      <!-- Scanlines overlay -->
      <div class="scanlines"></div>
      
      <!-- LCD Content -->
      <div class="lcd-content">
        <!-- Cover (small) -->
        <div class="lcd-cover" :style="coverStyle">
          <img 
            v-if="track.cover_url" 
            :src="track.cover_url" 
            alt=""
            class="cover-image"
          />
          <span v-else class="cover-text">{{ coverInitials }}</span>
        </div>
        
        <!-- Track info with marquee effect -->
        <div class="lcd-info">
          <div class="lcd-title" :class="{ marquee: shouldMarquee }">
            <span>{{ track.title || 'NO TRACK' }}</span>
          </div>
          <div class="lcd-artist">{{ track.artist || '---' }}</div>
          <div class="lcd-time">{{ formatTime(progress) }} / {{ formatTime(duration || track.duration) }}</div>
        </div>
        
        <!-- Playback indicator -->
        <div class="lcd-status">
          <div v-if="loading" class="status-loading">LOAD</div>
          <div v-else-if="isPlaying" class="status-play">
            <span class="blink">▶</span> PLAY
          </div>
          <div v-else class="status-pause">▮▮ STOP</div>
        </div>
      </div>
      
      <!-- Progress bar (LED style) -->
      <div class="led-progress">
        <div class="led-bar" v-for="i in 20" :key="i" :class="{ active: (i / 20) * 100 <= progressPercent, buffered: (i / 20) * 100 <= bufferedPercent }"></div>
      </div>
    </div>
    
    <!-- Physical buttons (outside LCD) -->
    <div class="physical-buttons">
      <button class="retro-btn" @click.stop="$emit('toggle')">
        <svg v-if="loading" class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke-width="3" stroke-opacity="0.3"/>
          <path d="M12 2a10 10 0 0 1 10 10" stroke-width="3" stroke-linecap="round"/>
        </svg>
        <span v-else-if="isPlaying">▮▮</span>
        <span v-else>▶</span>
      </button>
      
      <button class="retro-btn" @click.stop="$emit('next')">
        ▶▶
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

const shouldMarquee = computed(() => {
  return (props.track?.title?.length || 0) > 18
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* Retro LCD Player Styles */
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

.mini-player {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin: 12px 12px 8px;
  padding: 10px;
  background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
  border-radius: 12px;
  cursor: pointer;
  z-index: 60;
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.5),
    -4px -4px 10px rgba(60, 60, 60, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  border: 2px solid #333;
  position: relative;
}

/* LCD Screen Frame */
.lcd-frame {
  flex: 1;
  background: #0a1a12;
  border-radius: 6px;
  padding: 8px 10px;
  position: relative;
  overflow: hidden;
  border: 2px solid #1a2a1f;
  box-shadow: 
    inset 0 0 20px rgba(0, 0, 0, 0.8),
    inset 0 0 3px rgba(0, 255, 100, 0.1);
}

/* Scanlines effect */
.scanlines {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.15) 2px,
    rgba(0, 0, 0, 0.15) 4px
  );
  pointer-events: none;
  z-index: 10;
}

/* LCD Content */
.lcd-content {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

/* Cover in LCD */
.lcd-cover {
  width: 42px;
  height: 42px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  border: 1px solid rgba(0, 255, 100, 0.3);
  box-shadow: 0 0 8px rgba(0, 255, 100, 0.2);
}

.lcd-cover .cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.9) contrast(1.1);
}

.lcd-cover .cover-text {
  font-family: 'VT323', monospace;
  font-size: 18px;
  color: #00ff66;
  text-shadow: 0 0 8px rgba(0, 255, 100, 0.8);
}

/* LCD Info */
.lcd-info {
  flex: 1;
  min-width: 0;
  font-family: 'VT323', monospace;
}

.lcd-title {
  font-size: 18px;
  color: #00ff66;
  text-shadow: 
    0 0 10px rgba(0, 255, 100, 0.8),
    0 0 20px rgba(0, 255, 100, 0.4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.lcd-title.marquee span {
  display: inline-block;
  animation: marquee 8s linear infinite;
}

@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.lcd-artist {
  font-size: 14px;
  color: #00cc55;
  text-shadow: 0 0 6px rgba(0, 200, 80, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.8;
  margin-top: 2px;
}

.lcd-time {
  font-size: 12px;
  color: #00aa44;
  text-shadow: 0 0 4px rgba(0, 170, 68, 0.5);
  margin-top: 4px;
  letter-spacing: 2px;
}

/* Status indicator */
.lcd-status {
  font-family: 'VT323', monospace;
  font-size: 12px;
  color: #00ff66;
  text-shadow: 0 0 8px rgba(0, 255, 100, 0.8);
  white-space: nowrap;
  text-align: right;
  min-width: 50px;
}

.status-play {
  color: #00ff66;
}

.status-pause {
  color: #ffaa00;
  text-shadow: 0 0 8px rgba(255, 170, 0, 0.8);
}

.status-loading {
  color: #ff6600;
  text-shadow: 0 0 8px rgba(255, 100, 0, 0.8);
  animation: blink 0.5s infinite;
}

.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

/* LED Progress Bar */
.led-progress {
  display: flex;
  gap: 2px;
  margin-top: 8px;
  padding: 4px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 3px;
}

.led-bar {
  flex: 1;
  height: 4px;
  background: #0a2a15;
  border-radius: 1px;
  transition: background 0.1s, box-shadow 0.1s;
}

.led-bar.buffered {
  background: #1a3a25;
}

.led-bar.active {
  background: #00ff66;
  box-shadow: 0 0 4px rgba(0, 255, 100, 0.8);
}

.led-bar.active:nth-child(n+15) {
  background: #ffcc00;
  box-shadow: 0 0 4px rgba(255, 200, 0, 0.8);
}

.led-bar.active:nth-child(n+18) {
  background: #ff4400;
  box-shadow: 0 0 4px rgba(255, 68, 0, 0.8);
}

/* Physical Buttons */
.physical-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.retro-btn {
  width: 44px;
  height: 32px;
  border: none;
  background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 50%, #1a1a1a 100%);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aaa;
  font-family: 'VT323', monospace;
  font-size: 14px;
  letter-spacing: -1px;
  flex-shrink: 0;
  transition: all 0.1s ease;
  box-shadow: 
    2px 2px 4px rgba(0, 0, 0, 0.5),
    -1px -1px 2px rgba(80, 80, 80, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid #444;
}

.retro-btn:active {
  transform: translateY(1px);
  box-shadow: 
    1px 1px 2px rgba(0, 0, 0, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.3);
  background: linear-gradient(180deg, #2a2a2a 0%, #1a1a1a 50%, #0a0a0a 100%);
}

.retro-btn:first-child:active {
  color: #00ff66;
  text-shadow: 0 0 8px rgba(0, 255, 100, 0.8);
}

.spinner {
  animation: spin 1s linear infinite;
  color: #ff6600;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
