<template>
  <div class="mini-player" @click="$emit('expand')" @contextmenu.prevent="openMenu('track', track, 'player', $event)">
    <!-- Compact 2-row layout -->
    <div class="player-content">
      <!-- Row 1: Title + Status Icons -->
      <div class="player-row row-title">
        <div class="title-container">
          <div class="title-track" :class="{ 'marquee': shouldMarquee }">
            <span class="title-text">{{ displayText }}</span>
            <span v-if="shouldMarquee" class="title-text title-clone">{{ displayText }}</span>
          </div>
        </div>
        <div class="status-icons">
          <span v-if="playerStore.hdTrackInfo" class="status-icon hd-icon active" title="HD версия">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
            </svg>
          </span>
          <span v-else class="status-icon hd-icon" title="HD недоступен">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" opacity="0.3">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
            </svg>
          </span>
          <span 
            class="status-icon shuffle-icon" 
            :class="{ active: playerStore.shuffle }" 
            title="Перемешивание"
            @click.stop="$emit('toggleShuffle')"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
            </svg>
          </span>
          <span 
            class="status-icon repeat-icon" 
            :class="{ active: playerStore.repeatMode !== 'none' }" 
            :title="repeatTitle"
            @click.stop="$emit('toggleRepeat')"
          >
            <svg v-if="playerStore.repeatMode === 'one'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
            </svg>
          </span>
        </div>
      </div>
      
      <!-- Row 2: Play/Pause + Progress + Time -->
      <div class="player-row row-controls">
        <button class="play-btn" @click.stop="$emit('toggle')">
          <svg v-if="loading" class="spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <path d="M12 2a10 10 0 0 1 10 10"/>
          </svg>
          <svg v-else-if="isPlaying" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        
        <div class="progress-dots">
          <span 
            class="dot" 
            v-for="i in 24" 
            :key="i" 
            :class="getDotClass(i, 24)"
          ></span>
        </div>
        
        <span class="time-display">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { getDisplayTitle, getDisplayArtist } from '@/utils'

const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()

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

const emit = defineEmits(['expand', 'toggle', 'next', 'toggleShuffle', 'toggleRepeat'])

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
  switch (playerStore.repeatMode) {
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
   🎵 MINI PLAYER - Compact 2-Row Design
   ═══════════════════════════════════════════════════════════ */

.mini-player {
  display: flex;
  align-items: center;
  margin: 6px 10px;
  padding: 10px 14px;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-lg);
  cursor: pointer;
  overflow: visible;
  box-shadow: 
    6px 6px 12px var(--neu-shadow-dark),
    -3px -3px 8px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.03);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.mini-player:active {
  transform: scale(0.98);
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.player-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ─── Row Layout ─── */
.player-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

/* ─── Row 1: Title + Icons ─── */
.row-title {
  justify-content: space-between;
}

.title-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  mask-image: linear-gradient(90deg, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 90%, transparent 100%);
}

.title-track {
  display: inline-flex;
  white-space: nowrap;
}

.title-track.marquee {
  animation: marquee-scroll 12s linear infinite;
}

.title-text {
  color: var(--xm-text-primary);
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.title-clone {
  margin-left: 60px;
}

@keyframes marquee-scroll {
  0%, 5% { transform: translateX(0); }
  95%, 100% { transform: translateX(calc(-50% - 30px)); }
}

/* ─── Status Icons ─── */
.status-icons {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: var(--xm-text-muted);
  opacity: 0.4;
  transition: all 0.2s ease;
  cursor: pointer;
}

.status-icon:active {
  transform: scale(0.9);
}

.status-icon.active {
  opacity: 1;
  color: var(--xm-accent);
}

.status-icon.hd-icon.active {
  color: #ffd700;
}

.status-icon.hd-icon {
  cursor: default;
}

/* ─── Row 2: Controls ─── */
.row-controls {
  gap: 8px;
}

.play-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-primary);
  flex-shrink: 0;
  transition: all 0.15s ease;
  
  /* Rubber button style */
  background: var(--rubber-bg);
  box-shadow: 
    0 3px 6px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  border: 1px solid var(--rubber-border);
}

.play-btn:active {
  transform: scale(0.92) translateY(1px);
  background: var(--rubber-bg-pressed);
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.3);
}

.play-btn:active svg {
  color: var(--xm-accent);
  filter: drop-shadow(0 0 4px var(--xm-accent-glow));
}

/* ─── Progress Dots ─── */
.progress-dots {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
}

.dot {
  flex: 1;
  height: 4px;
  min-width: 2px;
  background: var(--lcd-dot-inactive, rgba(255, 255, 255, 0.15));
  border-radius: 2px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}

.dot.active {
  background: var(--xm-accent);
  box-shadow: 0 0 4px var(--xm-accent-glow);
}

.dot.buffered {
  background: rgba(0, 188, 212, 0.3);
}

.dot.next {
  background: var(--xm-accent);
  opacity: 0.5;
  animation: dot-blink 0.6s ease-in-out infinite;
}

@keyframes dot-blink {
  0%, 100% { opacity: 0.3; box-shadow: none; }
  50% { opacity: 1; box-shadow: 0 0 6px var(--xm-accent-glow); }
}

/* ─── Time Display ─── */
.time-display {
  font-size: 11px;
  font-weight: 600;
  color: var(--xm-text-muted);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  flex-shrink: 0;
  min-width: 70px;
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
