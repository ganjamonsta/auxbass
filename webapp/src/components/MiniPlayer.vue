<template>
  <div class="mini-player" @click="$emit('expand')" @contextmenu.prevent="openMenu('track', track, 'player', $event)">
    <!-- LCD Screen -->
    <div class="lcd-screen">
      <!-- Row 1: Title + Status Icons -->
      <div class="lcd-row row-title">
        <div class="lcd-title-container">
          <div class="lcd-title-track" :class="{ 'marquee': shouldMarquee }">
            <span class="lcd-title">{{ displayText }}</span>
            <span v-if="shouldMarquee" class="lcd-title lcd-title-clone">{{ displayText }}</span>
          </div>
        </div>
        <div class="lcd-indicators">
          <!-- Network issue indicator -->
          <span 
            v-if="networkMonitor.hasIssues.value" 
            class="lcd-indicator net-indicator active" 
            :class="{ pulse: networkMonitor.connectionState.value === 'reconnecting' }"
            :title="networkMonitor.connectionState.value === 'offline' ? 'Нет сети' : networkMonitor.connectionState.value === 'reconnecting' ? 'Восстановление...' : 'Медленная сеть'"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="1" y1="1" x2="23" y2="23"/>
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
              <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
              <line x1="12" y1="20" x2="12.01" y2="20"/>
            </svg>
          </span>
          <span v-if="playerStore.hdTrackInfo" class="lcd-indicator hd-indicator active" title="HD версия">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
            </svg>
          </span>
          <span v-else class="lcd-indicator hd-indicator" title="HD недоступен">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
            </svg>
          </span>
          <span 
            class="lcd-indicator like-indicator" 
            :class="{ active: isLiked }" 
            :title="isLiked ? 'Удалить из любимых' : 'Добавить в любимое'"
            @click.stop="$emit('like')"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </span>
          <span 
            class="lcd-indicator shuffle-indicator" 
            :class="{ active: playerStore.shuffle }" 
            title="Перемешивание"
            @click.stop="$emit('toggleShuffle')"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
            </svg>
          </span>
          <span 
            class="lcd-indicator repeat-indicator" 
            :class="{ active: playerStore.repeat !== 'none' }" 
            :title="repeatTitle"
            @click.stop="$emit('toggleRepeat')"
          >
            <svg v-if="playerStore.repeat === 'one'" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
            </svg>
          </span>
        </div>
      </div>
      
      <!-- Row 2: Progress Dots + Time + Controls -->
      <div class="lcd-row row-controls">
        <div class="lcd-progress">
          <span 
            class="lcd-dot" 
            v-for="i in 20" 
            :key="i" 
            :class="getDotClass(i, 20)"
          ></span>
        </div>
        
        <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
        
        <div class="lcd-buttons">
          <button class="lcd-btn" @click.stop="$emit('toggle')" title="Воспроизведение">
            <svg v-if="loading" class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            <svg v-else-if="isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
            </svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
          <button class="lcd-btn" @click.stop="$emit('next')" title="Следующий трек">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { getDisplayTitle, getDisplayArtist } from '@/utils'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'

const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()
const networkMonitor = useNetworkMonitor()

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
  },
  isLiked: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['expand', 'toggle', 'next', 'toggleShuffle', 'toggleRepeat', 'like'])

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

// Get class for each LED dot with configurable total
const getDotClass = (index, total = 24) => {
  const dotPercent = (index / total) * 100
  const prevDotPercent = ((index - 1) / total) * 100
  
  // Active (played) - red
  if (dotPercent <= progressPercent.value) {
    return 'active'
  }
  
  // Next dot to light up - blinking
  if (prevDotPercent < progressPercent.value && dotPercent > progressPercent.value) {
    return 'next'
  }
  
  // Buffered - blue
  if (dotPercent <= bufferedPercent.value) {
    return 'buffered'
  }
  
  return ''
}

const displayText = computed(() => {
  const artist = getDisplayArtist(props.track)
  const title = getDisplayTitle(props.track)
  return `${artist} — ${title}`
})

const shouldMarquee = computed(() => {
  return displayText.value.length > 30
})

const repeatTitle = computed(() => {
  switch (playerStore.repeat) {
    case 'one': return 'Повтор трека'
    case 'all': return 'Повтор всего'
    default: return 'Повтор выключен'
  }
})

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 MINI PLAYER - Nokia XpressMusic LCD Style (Compact 2-Row)
   ═══════════════════════════════════════════════════════════ */

.mini-player {
  display: flex;
  align-items: center;
  margin: 6px 10px;
  padding: 6px;
  background: var(--c-bg-2);
  border-radius: var(--r-lg);
  cursor: pointer;
  overflow: visible;
  box-shadow: 
    6px 6px 12px var(--sh-dark),
    -3px -3px 8px var(--sh-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.mini-player:active {
  transform: scale(0.98);
  box-shadow: 
    3px 3px 6px var(--sh-dark),
    -2px -2px 4px var(--sh-light);
}

/* ─── LCD Screen - Nokia XpressMusic Style ─── */
.lcd-screen {
  flex: 1;
  background: var(--lcd-bg);
  border-radius: var(--r-md);
  padding: 10px 12px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  border: 1px solid #1a2a40;
  box-shadow: 
    inset 0 2px 8px rgba(0, 0, 0, 0.8),
    0 1px 0 rgba(100, 150, 255, 0.1);
  min-width: 0;
  position: relative;
  overflow: visible;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Scanline effect for retro feel */
.lcd-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );
  pointer-events: none;
  border-radius: inherit;
}

/* ─── LCD Rows ─── */
.lcd-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  position: relative;
  z-index: 1;
}

/* ─── Row 1: Title + Indicators ─── */
.row-title {
  justify-content: space-between;
}

.lcd-title-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 90%, transparent 100%);
}

.lcd-title-track {
  display: inline-flex;
  white-space: nowrap;
}

.lcd-title-track.marquee {
  animation: marquee-scroll 12s linear infinite;
}

.lcd-title {
  color: var(--lcd-text);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-shadow: 0 0 8px var(--lcd-text-glow);
  white-space: nowrap;
  flex-shrink: 0;
}

.lcd-title-clone {
  margin-left: 60px;
}

@keyframes marquee-scroll {
  0%, 5% { transform: translateX(0); }
  95%, 100% { transform: translateX(calc(-50% - 30px)); }
}

/* ─── LCD Indicators (Icons) ─── */
.lcd-indicators {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.lcd-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  color: var(--lcd-dot-inactive);
  opacity: 0.4;
  transition: all 0.2s ease;
  cursor: pointer;
}

.lcd-indicator:active {
  transform: scale(0.9);
}

.lcd-indicator.active {
  opacity: 1;
  color: var(--lcd-text);
  text-shadow: 0 0 6px var(--lcd-text-glow);
}

.lcd-indicator.hd-indicator {
  cursor: default;
}

.lcd-indicator.hd-indicator.active {
  color: #ffd700;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.8);
}

.lcd-indicator.like-indicator:hover {
  opacity: 0.85;
}

.lcd-indicator.like-indicator.active {
  opacity: 1;
  color: #ff4b7b;
  text-shadow: 0 0 8px rgba(255, 75, 123, 0.7);
}

.lcd-indicator.like-indicator.active svg {
  filter: drop-shadow(0 0 4px rgba(255, 75, 123, 0.8));
}

.lcd-indicator.net-indicator.active {
  color: #ff6b6b;
  text-shadow: 0 0 8px rgba(255, 107, 107, 0.8);
  cursor: default;
}

.lcd-indicator.net-indicator.pulse {
  animation: net-pulse 1.5s ease-in-out infinite;
}

@keyframes net-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ─── Row 2: Controls ─── */
.row-controls {
  gap: 8px;
}

/* ─── LCD Buttons Group (Play + Next) ─── */
.lcd-buttons {
  display: flex;
  flex-shrink: 0;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.lcd-btn {
  width: 32px;
  height: 26px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--lcd-text);
  transition: all 0.15s ease;
  position: relative;
}

/* Divider between buttons */
.lcd-btn:first-child::after {
  content: '';
  position: absolute;
  right: 0;
  top: 4px;
  bottom: 4px;
  width: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.lcd-btn:active {
  background: rgba(0, 0, 0, 0.3);
}

.lcd-btn:active svg {
  color: var(--c-accent);
  filter: drop-shadow(0 0 4px var(--c-accent-glow));
}

/* ─── LED Progress Dots ─── */
.lcd-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
}

.lcd-dot {
  flex: 1;
  height: 4px;
  min-width: 2px;
  background: var(--lcd-dot-inactive);
  border-radius: 2px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.lcd-dot.active {
  background: var(--c-accent);
  box-shadow: 0 0 4px var(--c-accent-glow);
}

.lcd-dot.buffered {
  background: rgba(0, 188, 212, 0.3);
}

.lcd-dot.next {
  background: var(--c-accent);
  opacity: 0.5;
  animation: dot-blink 0.6s ease-in-out infinite;
}

@keyframes dot-blink {
  0%, 100% { opacity: 0.3; box-shadow: none; }
  50% { opacity: 1; box-shadow: 0 0 6px var(--c-accent-glow); }
}

/* ─── Time Display ─── */
.lcd-time {
  font-size: 11px;
  font-weight: 600;
  color: var(--lcd-text);
  text-shadow: 0 0 6px var(--lcd-text-glow);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  flex-shrink: 0;
  min-width: 65px;
  text-align: right;
}

/* ─── Utilities ─── */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
