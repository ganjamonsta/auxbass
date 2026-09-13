<template>
  <div class="desktop-player" :class="{ playing: isPlaying }" @contextmenu.prevent="openMenu('track', track, 'player', $event)">
    <!-- Left side - Volume knob -->
    <div class="player-left">
      <div 
        class="volume-knob"
        :class="{ adjusting: isAdjustingVolume }"
        @mousedown="startVolumeAdjust"
        @wheel.prevent="handleVolumeWheel"
        :style="{ '--rotation': volumeRotation + 'deg' }"
        :title="`Громкость: ${Math.round(volume * 100)}%`"
      >
        <svg class="volume-arc-svg" viewBox="0 0 58 58">
          <circle
            class="volume-arc-bg"
            cx="29"
            cy="29"
            r="26"
            fill="none"
          />
          <circle
            v-if="volume > 0.005"
            class="volume-arc-glow"
            cx="29"
            cy="29"
            r="26"
            fill="none"
            :stroke-dasharray="`${volumeArcLength} 163.36`"
          />
          <circle
            v-if="volume > 0.005"
            class="volume-arc-fill"
            cx="29"
            cy="29"
            r="26"
            fill="none"
            :stroke-dasharray="`${volumeArcLength} 163.36`"
          />
        </svg>
        <div class="knob-outer">
          <div class="knob-inner">
            <div class="knob-indicator"></div>
          </div>
        </div>
      </div>
      <span class="vol-label">VOL</span>
    </div>

    <!-- Control buttons -->
    <div class="player-controls">
      <button 
        class="ctrl-btn mode" 
        :class="{ active: shuffle }" 
        @click="playerStore.toggleShuffle()" 
        :title="shuffle ? 'Случайно: включено' : 'Случайно: выключено'"
      >
        <span class="btn-icon"><Shuffle :size="14" /></span>
      </button>
      <button class="ctrl-btn" @click="playerStore.prev()" title="Предыдущий трек">
        <span class="btn-icon"><SkipBack :size="14" /></span>
      </button>
      <button class="ctrl-btn play-btn" @click="playerStore.togglePlay()" :title="isPlaying ? 'Пауза' : 'Воспроизведение'">
        <span class="btn-icon"><Pause v-if="isPlaying" :size="16" fill="currentColor" /><Play v-else :size="16" fill="currentColor" /></span>
      </button>
      <button class="ctrl-btn" @click="playerStore.next()" title="Следующий трек">
        <span class="btn-icon"><SkipForward :size="14" /></span>
      </button>
      <button 
        class="ctrl-btn mode" 
        :class="{ active: repeat !== 'none' }" 
        @click="playerStore.toggleRepeat()" 
        :title="repeatTitle"
      >
        <span class="btn-icon">
          <Repeat1 v-if="repeat === 'one'" :size="14" />
          <Repeat v-else :size="14" />
        </span>
      </button>
    </div>

    <!-- Center - Neon Waveform Display -->
    <div class="lcd-panel">
      <div class="lcd-frame">
        <div class="lcd-screen" @click="handleLcdClick">
          <!-- Title row -->
          <div class="lcd-title-row">
            <!-- Network issue indicator -->
            <span 
              v-if="networkMonitor.hasIssues.value" 
              class="lcd-net-icon"
              :class="{ pulse: networkMonitor.connectionState.value === 'reconnecting' }"
              :title="networkMonitor.connectionState.value === 'offline' ? 'Нет сети' : networkMonitor.connectionState.value === 'reconnecting' ? 'Восстановление...' : 'Медленная сеть'"
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="1" y1="1" x2="23" y2="23"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.56 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
              </svg>
            </span>
            <VfdSegmentDisplay 
              :track="track"
              :nextTrack="nextTrack"
              :queueIndex="playerStore.queueIndex"
              :queueLength="playerStore.queue.length"
              :isPlaying="isPlaying"
              :volume="volume"
            />
          </div>

          <!-- Waveform & Progress row -->
          <div class="lcd-waveform-row">
            <div class="lcd-time-col left">
              <span class="lcd-status" style="margin-right: 4px; display: flex; align-items: center;">
                <Play v-if="isPlaying" :size="10" fill="currentColor" />
                <Square v-else :size="10" fill="currentColor" />
              </span>
              <span class="lcd-time">{{ formatTime(progress) }}</span>
            </div>

            <!-- Interactive Neon Waveform Scrubber -->
            <div 
              class="waveform-container" 
              ref="waveformContainer"
              @click="handleWaveformClick"
              @mousedown="startSeek"
              @mousemove="handleWaveformHover"
              @mouseleave="handleWaveformLeave"
              title="Перемотка трека"
            >
              <canvas ref="waveformCanvas" class="waveform-canvas"></canvas>
              
              <!-- Hover line and tooltip -->
              <div 
                v-if="hoverPercent !== null" 
                class="waveform-hover-marker"
                :style="{ left: (hoverPercent * 100) + '%' }"
              >
                <div class="waveform-hover-tip">
                  {{ formatTime(hoverPercent * duration) }}
                </div>
              </div>
            </div>

            <div class="lcd-time-col right">
              <span class="lcd-time">{{ formatTime(duration) }}</span>
            </div>
          </div>

          <!-- Bottom: Equalizer + Audio Format badge -->
          <div class="lcd-bottom-row">
            <div class="lcd-eq">
              <div 
                v-for="i in 18" 
                :key="i" 
                class="eq-bar"
                :style="{ height: getEqHeight(i) + '%' }"
              ></div>
            </div>
            <div class="lcd-format-badge">
              <span v-if="playerStore.hdTrackInfo" class="badge-hd">HD 24-BIT</span>
              <span v-else class="badge-std">STEREO AUDIO</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right side - Cover & controls -->
    <div class="player-right">
      <div class="cover-display" @click="$emit('expand')">
        <div class="cover-art" :style="coverStyle">
          <img v-if="track?.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.LARGE)" alt="" />
          <span v-else class="cover-text">{{ coverInitials }}</span>
        </div>
        <div class="vinyl-disc" :class="{ spinning: isPlaying }">
          <div class="vinyl-groove"></div>
          <div class="vinyl-groove"></div>
          <div class="vinyl-groove"></div>
          <div class="vinyl-center"></div>
        </div>
      </div>
      
      <!-- Share button -->
      <button 
        v-if="track"
        class="share-ctrl-btn" 
        @click="handleShare"
        title="Поделиться треком"
      >
        <Share2 :size="16" />
      </button>

      <!-- Like button -->
      <button 
        class="like-btn" 
        :class="{ liked: isLiked }" 
        @click="handleToggleLike"
        title="Лайк"
      >
        <svg v-if="isLiked" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
        </svg>
      </button>
      
      <button class="mute-btn" :class="{ muted: isMuted }" @click="playerStore.toggleMute()">
        <VolumeX v-if="isMuted" :size="16" /><Volume2 v-else :size="16" />
      </button>

      <!-- Toggle Now Playing Sidebar button -->
      <button 
        class="sidebar-ctrl-btn" 
        :class="{ active: uiStore.isNowPlayingSidebarVisible }" 
        @click="uiStore.toggleNowPlayingSidebar()"
        :title="uiStore.isNowPlayingSidebarVisible ? 'Скрыть панель «Сейчас играет»' : 'Показать панель «Сейчас играет»'"
        aria-label="Панель Сейчас играет"
      >
        <PanelRightClose v-if="uiStore.isNowPlayingSidebarVisible" :size="16" />
        <PanelRight v-else :size="16" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { getCoverUrl, CoverSize } from '@/utils'
import { Play, Square, Pause, Volume2, VolumeX, SkipBack, SkipForward, Shuffle, Repeat, Repeat1, Share2, PanelRightClose, PanelRight } from 'lucide-vue-next'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'
import { useShare } from '@/composables/useShare'
import VfdSegmentDisplay from './VfdSegmentDisplay.vue'

const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()
const { openMenu } = useContextMenu()
const { openShare } = useShare()
const networkMonitor = useNetworkMonitor()

const handleShare = () => {
  if (!track.value?.id) return
  openShare({
    type: 'track',
    id: track.value.id,
    title: track.value.title || track.value.file_name || 'Трек',
    subtitle: track.value.artist || 'Неизвестен',
    coverUrl: track.value.cover_url || '',
  })
}

const emit = defineEmits(['expand'])

// Computed from stores
const track = computed(() => playerStore.currentTrack)
const isPlaying = computed(() => playerStore.isPlaying)
const progress = computed(() => playerStore.progress)
const duration = computed(() => playerStore.duration)
const buffered = computed(() => playerStore.buffered)
const volume = computed(() => playerStore.volume)
const isMuted = computed(() => playerStore.isMuted)
const shuffle = computed(() => playerStore.shuffle)
const repeat = computed(() => playerStore.repeat)

const repeatTitle = computed(() => {
  if (repeat.value === 'one') return 'Повтор одного трека'
  if (repeat.value === 'all') return 'Повтор всех треков'
  return 'Повтор выключен'
})

const isLiked = computed(() => {
  if (!track.value?.id) return false
  if (libraryStore.isTrackLiked(track.value.id)) return true
  return track.value.is_liked === true
})

// Handle LCD click - open full player (but not on waveform or VFD display)
const handleLcdClick = (e) => {
  if (isSeeking.value || e.target.closest('.waveform-container') || e.target.closest('.vfd-display')) {
    return
  }
  emit('expand')
}

// Volume knob
const isAdjustingVolume = ref(false)
const startY = ref(0)
const startVolume = ref(0)

const volumeRotation = computed(() => {
  return -135 + (volume.value * 270)
})

const volumeArcLength = computed(() => {
  const v = Math.max(0, Math.min(1, Number(volume.value) || 0))
  return (v * 122.52).toFixed(2)
})

const startVolumeAdjust = (e) => {
  isAdjustingVolume.value = true
  startY.value = e.clientY
  startVolume.value = volume.value
  document.addEventListener('mousemove', onVolumeMove)
  document.addEventListener('mouseup', stopVolumeAdjust)
}

const onVolumeMove = (e) => {
  if (!isAdjustingVolume.value) return
  const delta = (startY.value - e.clientY) / 100
  const newVolume = Math.max(0, Math.min(1, startVolume.value + delta))
  playerStore.setVolume(newVolume)
}

const stopVolumeAdjust = () => {
  isAdjustingVolume.value = false
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', stopVolumeAdjust)
}

const handleVolumeWheel = (e) => {
  const step = e.shiftKey ? 0.01 : 0.05
  const delta = e.deltaY > 0 ? -step : step
  const newVolume = Math.max(0, Math.min(1, volume.value + delta))
  playerStore.setVolume(newVolume)
}

// Next track in queue for display
const nextTrack = computed(() => {
  if (!playerStore.queue || playerStore.queue.length === 0) return null
  if (playerStore.shuffle) {
    const nextIdx = playerStore.shuffleOrder[playerStore.shuffleIndex + 1]
    return nextIdx !== undefined ? playerStore.queue[nextIdx] : null
  }
  const nextIdx = playerStore.queueIndex + 1
  return nextIdx < playerStore.queue.length ? playerStore.queue[nextIdx] : null
})



// Deterministic hash-based waveform peak generator
// Generates musical amplitude peaks (0.15 - 0.98) with zero network traffic & zero latency
const peaksCache = new Map()

const getWaveformPeaks = (trackId, title, count = 120) => {
  const cacheKey = `${trackId || title || 'default'}_${count}`
  if (peaksCache.has(cacheKey)) {
    return peaksCache.get(cacheKey)
  }

  // Hash seed from track id / title
  const seedStr = `${trackId || ''}_${title || 'tg_player'}`
  let seed = 0
  for (let i = 0; i < seedStr.length; i++) {
    seed = (seed * 31 + seedStr.charCodeAt(i)) >>> 0
  }

  let state = seed || 123456789
  const rng = () => {
    state ^= state << 13
    state ^= state >>> 17
    state ^= state << 5
    return ((state >>> 0) % 10000) / 10000
  }

  const peaks = []
  const freq1 = 2 + (seed % 4)
  const freq2 = 5 + ((seed >> 2) % 6)
  const freq3 = 11 + ((seed >> 4) % 8)

  for (let i = 0; i < count; i++) {
    const t = i / count

    // Musical envelope: rising intro (8%), stable dynamic body, tapering outro (8%)
    let envelope = 1
    if (t < 0.08) {
      envelope = 0.35 + 0.65 * (t / 0.08)
    } else if (t > 0.92) {
      envelope = 0.35 + 0.65 * ((1 - t) / 0.08)
    }

    const wave = 
      0.35 * Math.sin(t * Math.PI * freq1) +
      0.25 * Math.sin(t * Math.PI * freq2 + 1.2) +
      0.15 * Math.sin(t * Math.PI * freq3 + 2.4)

    const jitter = (rng() - 0.5) * 0.22
    let val = (0.55 + wave * 0.35 + jitter) * envelope
    val = Math.max(0.16, Math.min(0.96, val))
    peaks.push(val)
  }

  peaksCache.set(cacheKey, peaks)
  return peaks
}

const waveformCanvas = ref(null)
const waveformContainer = ref(null)
const hoverPercent = ref(null)
const isSeeking = ref(false)

const drawWaveform = () => {
  const canvas = waveformCanvas.value
  const container = waveformContainer.value
  if (!canvas || !container) return

  const rect = container.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height

  ctx.clearRect(0, 0, w, h)

  const barWidth = 2.5
  const barGap = 1.5
  const step = barWidth + barGap
  const numBars = Math.floor(w / step)
  if (numBars <= 0) return

  const peaks = getWaveformPeaks(track.value?.id, track.value?.title, numBars)
  const currentP = Math.max(0, Math.min(1, progress.value / (duration.value || 1)))
  const hoverP = hoverPercent.value
  const cy = h / 2

  for (let i = 0; i < numBars; i++) {
    const x = i * step + barWidth / 2
    const barProgress = x / w
    const barH = Math.max(3, peaks[i] * (h * 0.88))
    const top = cy - barH / 2
    const isPlayed = barProgress <= currentP
    const isHovered = hoverP !== null && barProgress <= hoverP

    const gradient = ctx.createLinearGradient(0, top, 0, top + barH)
    if (isPlayed) {
      gradient.addColorStop(0, '#00f0ff')
      gradient.addColorStop(0.5, '#38bdf8')
      gradient.addColorStop(1, '#0284c7')
      ctx.fillStyle = gradient
      ctx.shadowColor = 'rgba(0, 240, 255, 0.45)'
      ctx.shadowBlur = 4
    } else if (isHovered) {
      gradient.addColorStop(0, 'rgba(0, 240, 255, 0.65)')
      gradient.addColorStop(1, 'rgba(56, 189, 248, 0.45)')
      ctx.fillStyle = gradient
      ctx.shadowBlur = 0
    } else {
      gradient.addColorStop(0, 'rgba(0, 240, 255, 0.24)')
      gradient.addColorStop(1, 'rgba(0, 180, 216, 0.12)')
      ctx.fillStyle = gradient
      ctx.shadowBlur = 0
    }

    ctx.beginPath()
    if (ctx.roundRect) {
      ctx.roundRect(i * step, top, barWidth, barH, 1.2)
    } else {
      ctx.rect(i * step, top, barWidth, barH)
    }
    ctx.fill()
  }
}

// Waveform seeking and hover interactions
const handleWaveformClick = (e) => {
  const container = waveformContainer.value
  if (!container || !duration.value) return
  const rect = container.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  playerStore.seek(percent * duration.value)
}

const handleWaveformHover = (e) => {
  const container = waveformContainer.value
  if (!container || isSeeking.value) return
  const rect = container.getBoundingClientRect()
  hoverPercent.value = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  drawWaveform()
}

const handleWaveformLeave = () => {
  if (isSeeking.value) return
  hoverPercent.value = null
  drawWaveform()
}

const startSeek = (e) => {
  isSeeking.value = true
  handleProgressSeek(e)
  document.addEventListener('mousemove', onSeekMove)
  document.addEventListener('mouseup', stopSeek)
}

const handleProgressSeek = (e) => {
  const container = waveformContainer.value
  if (!container || !duration.value) return
  const rect = container.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  hoverPercent.value = percent
  playerStore.seek(percent * duration.value)
  drawWaveform()
}

const onSeekMove = (e) => {
  if (!isSeeking.value) return
  handleProgressSeek(e)
}

const stopSeek = () => {
  isSeeking.value = false
  hoverPercent.value = null
  document.removeEventListener('mousemove', onSeekMove)
  document.removeEventListener('mouseup', stopSeek)
  drawWaveform()
}

// Cover
const coverStyle = computed(() => {
  if (track.value?.cover_url) return {}
  const str = track.value?.title || 'Music'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 30%) 0%, hsl(${(hue + 40) % 360}, 50%, 20%) 100%)`
  }
})

const coverInitials = computed(() => {
  const title = track.value?.title || 'M'
  return title.substring(0, 2).toUpperCase()
})

// Time format
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Equalizer animation
const eqValues = ref(Array(18).fill(20))

const getEqHeight = (index) => {
  return eqValues.value[index - 1] || 15
}

let eqInterval = null

const animateEq = () => {
  if (isPlaying.value) {
    eqValues.value = eqValues.value.map(() => Math.random() * 65 + 15)
  } else {
    eqValues.value = eqValues.value.map(() => 15)
  }
}

// Like handler
const handleToggleLike = async () => {
  if (track.value?.id) {
    const current = isLiked.value
    await libraryStore.toggleLike(track.value.id, current)
  }
}

// Watch for progress changes to redraw waveform
watch(() => playerStore.progress, () => {
  if (!isSeeking.value) {
    drawWaveform()
  }
})

// Watch for track changes and redraw waveform
watch([track, duration], () => {
  nextTick(() => {
    drawWaveform()
  })
})

const handleResize = () => {
  drawWaveform()
}

onMounted(() => {
  eqInterval = setInterval(animateEq, 100)
  nextTick(() => {
    drawWaveform()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  clearInterval(eqInterval)
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('mousemove', onVolumeMove)
  document.removeEventListener('mouseup', stopVolumeAdjust)
  document.removeEventListener('mousemove', onSeekMove)
  document.removeEventListener('mouseup', stopSeek)
})
</script>

<style scoped>
.desktop-player {
  height: var(--desktop-player-height);
  background: linear-gradient(180deg, #1a1a1a 0%, #0d0d0d 50%, #1a1a1a 100%);
  border-top: 1px solid #333;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 -4px 20px rgba(0, 0, 0, 0.5);
  position: sticky;
  bottom: 0;
  left: 0;
  right: 0;
  overflow: visible;
  z-index: 200;
}

.desktop-player::before {
  content: '';
  position: absolute;
  inset: 0;
  background: 
    linear-gradient(90deg, rgba(0,0,0,0.3) 0%, transparent 10%, transparent 90%, rgba(0,0,0,0.3) 100%);
  pointer-events: none;
}

/* Volume Knob */
.player-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.volume-knob {
  position: relative;
  width: 50px;
  height: 50px;
  cursor: pointer;
  user-select: none;
}

.volume-arc-svg {
  position: absolute;
  top: -4px;
  left: -4px;
  width: 58px;
  height: 58px;
  pointer-events: none;
  transform: rotate(135deg);
  transform-origin: center;
  overflow: visible;
  z-index: 1;
}

.volume-arc-bg {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 2.5;
  stroke-dasharray: 122.52 163.36;
  stroke-linecap: round;
  transition: stroke 0.2s;
}

.volume-knob:hover .volume-arc-bg {
  stroke: rgba(0, 240, 255, 0.2);
}

.volume-arc-glow {
  stroke: #00f0ff;
  stroke-width: 5;
  stroke-linecap: round;
  opacity: 0.55;
  filter: blur(2.5px);
  transition: stroke-dasharray 0.06s ease-out;
}

.volume-arc-fill {
  stroke: #00f0ff;
  stroke-width: 2.5;
  stroke-linecap: round;
  filter: drop-shadow(0 0 3px #00f0ff) drop-shadow(0 0 7px rgba(0, 240, 255, 0.8));
  transition: stroke-dasharray 0.06s ease-out;
}

.volume-knob:hover .volume-arc-glow,
.volume-knob.adjusting .volume-arc-glow {
  opacity: 0.8;
  stroke-width: 6;
  filter: blur(3px);
}

.volume-knob:hover .volume-arc-fill,
.volume-knob.adjusting .volume-arc-fill {
  stroke: #5ce9ff;
  filter: drop-shadow(0 0 5px #00f0ff) drop-shadow(0 0 10px rgba(0, 240, 255, 0.95));
}

.volume-knob.adjusting .knob-inner,
.volume-knob.adjusting .volume-arc-fill,
.volume-knob.adjusting .volume-arc-glow {
  transition: none !important;
}

.knob-outer {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
  box-shadow: 
    4px 4px 10px rgba(0, 0, 0, 0.5),
    -2px -2px 8px rgba(255, 255, 255, 0.05),
    inset 0 0 20px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.knob-inner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(145deg, #333, #222);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.5);
  position: relative;
  transform: rotate(var(--rotation));
  transition: transform 0.1s ease;
}

.knob-indicator {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 3px;
  height: 8px;
  background: #4DC3FF;
  border-radius: 2px;
  box-shadow: 0 0 8px #4DC3FF, 0 0 16px rgba(77, 195, 255, 0.6);
}

.vol-label {
  font-size: 8px;
  color: #4DC3FF;
  text-shadow: 0 0 5px rgba(77, 195, 255, 0.6);
  font-weight: bold;
  letter-spacing: 1px;
  transition: color 0.2s, text-shadow 0.2s;
}

.player-left:hover .vol-label,
.volume-knob.adjusting + .vol-label {
  color: #00f0ff;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.9);
}

/* LCD Panel */
.lcd-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
}

.lcd-frame {
  flex: 1;
  min-width: 0;
  background: #0a0a0a;
  border-radius: 4px;
  padding: 3px;
  box-shadow: 
    inset 2px 2px 6px rgba(0, 0, 0, 0.8),
    inset -1px -1px 3px rgba(255, 255, 255, 0.05);
}

.lcd-screen {
  background: linear-gradient(180deg, #071018 0%, #03080e 50%, #071018 100%);
  border: 1px solid rgba(0, 240, 255, 0.15);
  border-radius: 4px;
  padding: 6px 14px 4px;
  height: 74px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  overflow: hidden;
  box-shadow: inset 0 0 24px rgba(0, 0, 0, 0.9), 0 0 10px rgba(0, 240, 255, 0.05);
}

.lcd-title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  height: 22px;
  position: relative;
}

.lcd-net-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  color: #ff6b6b;
  filter: drop-shadow(0 0 4px rgba(255, 107, 107, 0.8));
}

.lcd-net-icon.pulse {
  animation: desktop-net-pulse 1.5s ease-in-out infinite;
}

@keyframes desktop-net-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Waveform Row */
.lcd-waveform-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  height: 32px;
  position: relative;
}

.lcd-time-col {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.lcd-status {
  color: #00f0ff;
  font-size: 11px;
  text-shadow: 0 0 8px rgba(0, 240, 255, 0.8);
  flex-shrink: 0;
}

.lcd-time {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #7dd3fc;
  text-shadow: 0 0 5px rgba(0, 240, 255, 0.6);
  min-width: 32px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.waveform-container {
  flex: 1;
  height: 30px;
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.waveform-hover-marker {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1.5px;
  background: #ffffff;
  pointer-events: none;
  transform: translateX(-50%);
  box-shadow: 0 0 8px #00f0ff, 0 0 14px #38bdf8;
  z-index: 2;
}

.waveform-hover-tip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 3px;
  padding: 2px 6px;
  font-family: 'Courier New', monospace;
  font-size: 9.5px;
  font-weight: 700;
  color: #fff;
  background: rgba(4, 12, 20, 0.95);
  border: 1px solid #00f0ff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.8), 0 0 6px rgba(0, 240, 255, 0.4);
  white-space: nowrap;
}

/* Bottom Row */
.lcd-bottom-row {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  height: 12px;
}

.lcd-eq {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  height: 12px;
}

.eq-bar {
  width: 3px;
  min-height: 2px;
  background: linear-gradient(180deg, #00f0ff, #0284c7);
  border-radius: 1px;
  box-shadow: 0 0 4px rgba(0, 240, 255, 0.7);
  transition: height 0.1s ease;
}

.lcd-format-badge {
  position: absolute;
  right: 0;
  font-family: 'Courier New', monospace;
  font-size: 8.5px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.badge-hd {
  color: #00f0ff;
  text-shadow: 0 0 6px rgba(0, 240, 255, 0.7);
}

.badge-std {
  color: rgba(0, 240, 255, 0.35);
}

/* Control Buttons */
.player-controls,
.lcd-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-shrink: 0;
}

.ctrl-btn {
  background: linear-gradient(180deg, #2a2a2a, #1a1a1a);
  border: 1px solid #333;
  border-radius: 4px;
  color: #7DD3FC;
  font-size: 12px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ctrl-btn:hover {
  background: linear-gradient(180deg, #333, #222);
  color: #4DC3FF;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
}

.ctrl-btn:active {
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.5);
  transform: translateY(1px);
}

.ctrl-btn.play-btn {
  padding: 8px 16px;
  font-size: 16px;
}

.ctrl-btn.mode {
  padding: 8px 10px;
}

.ctrl-btn.mode.active {
  color: #4DC3FF;
  text-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
  border-color: #4DC3FF;
  box-shadow: 
    2px 2px 5px rgba(0, 0, 0, 0.5),
    0 0 10px rgba(77, 195, 255, 0.3);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-label {
  font-weight: bold;
  letter-spacing: 1px;
}

/* Right Side */
.player-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cover-display {
  position: relative;
  width: 60px;
  height: 60px;
  cursor: pointer;
}

.cover-art {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: bold;
  position: relative;
  z-index: 2;
}

.cover-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vinyl-disc {
  position: absolute;
  width: 50px;
  height: 50px;
  right: -18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
  border-radius: 50%;
  z-index: 1;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.5);
}

.vinyl-disc.spinning {
  animation: spin-vinyl 3s linear infinite;
}

@keyframes spin-vinyl {
  to { transform: translateY(-50%) rotate(360deg); }
}

.vinyl-groove {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.vinyl-groove:nth-child(1) { inset: 15%; }
.vinyl-groove:nth-child(2) { inset: 25%; }
.vinyl-groove:nth-child(3) { inset: 35%; }

.vinyl-center {
  position: absolute;
  inset: 40%;
  background: #4DC3FF;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(77, 195, 255, 0.6);
}

.mute-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.15s;
}

.mute-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.mute-btn.muted {
  filter: grayscale(1);
  opacity: 0.5;
}

.like-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-ctrl-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.share-ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #60a5fa;
}

.sidebar-ctrl-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.sidebar-ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.sidebar-ctrl-btn.active {
  color: var(--c-accent, #1db954);
}

.like-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

.like-btn.liked {
  color: #ff4b7b;
  filter: drop-shadow(0 0 6px rgba(255, 75, 123, 0.6));
}

.like-btn.liked:hover {
  background: rgba(255, 75, 123, 0.15);
}

/* Playing state */
.desktop-player.playing {
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 -4px 20px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(77, 195, 255, 0.15);
}

.desktop-player.playing .lcd-frame {
  box-shadow: 
    inset 2px 2px 6px rgba(0, 0, 0, 0.8),
    inset -1px -1px 3px rgba(255, 255, 255, 0.05),
    0 0 20px rgba(77, 195, 255, 0.25);
}
</style>
