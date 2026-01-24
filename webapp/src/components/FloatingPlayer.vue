<template>
  <div 
    class="floating-player"
    :class="{ dragging: isDragging, minimized: isMinimized }"
    :style="playerStyle"
    @mousedown="startDrag"
  >
    <!-- Drag handle -->
    <div class="drag-handle" @dblclick="toggleMinimize">
      <div class="handle-dots">
        <span></span><span></span><span></span>
      </div>
    </div>

    <!-- Minimized state -->
    <div v-if="isMinimized" class="minimized-content" @click="toggleMinimize">
      <div class="mini-cover" :style="coverStyle">
        <img v-if="track?.cover_url" :src="track.cover_url" alt="" />
        <span v-else class="cover-text">{{ coverInitials }}</span>
      </div>
      <button class="mini-play-btn" @click.stop="$emit('toggle')">
        <svg v-if="isPlaying" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <rect x="6" y="4" width="4" height="16" rx="1"/>
          <rect x="14" y="4" width="4" height="16" rx="1"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
    </div>

    <!-- Full player content -->
    <div v-else class="player-content">
      <!-- LCD Screen -->
      <div class="lcd-container">
        <div class="lcd-screen">
          <div class="lcd-row main">
            <span class="lcd-status">{{ isPlaying ? '▶' : '■' }}</span>
            <div class="lcd-title-wrap">
              <div class="lcd-title" :class="{ marquee: shouldMarquee }">
                <span>{{ displayText }}</span>
                <span v-if="shouldMarquee" class="clone">{{ displayText }}</span>
              </div>
            </div>
          </div>
          <div class="lcd-row sub">
            <span class="lcd-time">{{ formatTime(progress) }}</span>
            <div class="lcd-progress-dots">
              <span 
                v-for="i in 12" 
                :key="i" 
                class="dot"
                :class="getDotClass(i, 12)"
              ></span>
            </div>
            <span class="lcd-time">{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>

      <!-- Cover Art -->
      <div class="cover-section">
        <div class="cover-art" :style="coverStyle" @click="$emit('expand')">
          <img v-if="track?.cover_url" :src="track.cover_url" alt="" />
          <span v-else class="cover-text">{{ coverInitials }}</span>
          
          <!-- Vinyl effect -->
          <div class="vinyl-overlay" :class="{ spinning: isPlaying }">
            <div class="vinyl-ring"></div>
            <div class="vinyl-ring"></div>
            <div class="vinyl-center"></div>
          </div>
        </div>
      </div>

      <!-- Controls -->
      <div class="controls-section">
        <!-- Transport controls -->
        <div class="transport">
          <button class="ctrl-btn" @click="$emit('prev')" title="Предыдущий">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
            </svg>
          </button>
          
          <button class="ctrl-btn play" @click="$emit('toggle')">
            <svg v-if="loading" class="spin" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a10 10 0 0 1 10 10"/>
            </svg>
            <svg v-else-if="isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1"/>
              <rect x="14" y="4" width="4" height="16" rx="1"/>
            </svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
          
          <button class="ctrl-btn" @click="$emit('next')" title="Следующий">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
            </svg>
          </button>
        </div>

        <!-- Mode buttons -->
        <div class="modes">
          <button 
            class="mode-btn" 
            :class="{ active: shuffle }"
            @click="$emit('toggleShuffle')"
            title="Перемешать"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
            </svg>
          </button>
          
          <button 
            class="mode-btn"
            :class="{ active: repeat !== 'none' }"
            @click="$emit('toggleRepeat')"
            title="Повтор"
          >
            <svg v-if="repeat === 'one'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
            </svg>
          </button>
        </div>

        <!-- Volume -->
        <div class="volume-control">
          <button class="vol-btn" @click="$emit('toggleMute')">
            <svg v-if="isMuted || volume === 0" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
            <svg v-else-if="volume < 0.5" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </svg>
          </button>
          <div class="vol-slider-wrap">
            <input 
              type="range"
              class="vol-slider"
              min="0"
              max="1"
              step="0.01"
              :value="volume"
              @input="$emit('setVolume', Number($event.target.value))"
            />
          </div>
        </div>
      </div>

      <!-- Expand button -->
      <button class="expand-btn" @click="$emit('expand')" title="Развернуть">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  loading: Boolean,
  progress: { type: Number, default: 0 },
  duration: { type: Number, default: 0 },
  buffered: { type: Number, default: 0 },
  volume: { type: Number, default: 1 },
  isMuted: Boolean,
  shuffle: Boolean,
  repeat: { type: String, default: 'none' }
})

defineEmits([
  'toggle', 'prev', 'next', 'expand',
  'toggleShuffle', 'toggleRepeat', 'toggleMute', 'setVolume'
])

// Dragging
const isDragging = ref(false)
const isMinimized = ref(false)
const position = ref({ x: 20, y: window.innerHeight - 220 })
const dragOffset = ref({ x: 0, y: 0 })

const playerStyle = computed(() => ({
  left: `${position.value.x}px`,
  top: `${position.value.y}px`
}))

const startDrag = (e) => {
  if (e.target.closest('button, input')) return
  isDragging.value = true
  dragOffset.value = {
    x: e.clientX - position.value.x,
    y: e.clientY - position.value.y
  }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!isDragging.value) return
  const x = Math.max(0, Math.min(window.innerWidth - 300, e.clientX - dragOffset.value.x))
  const y = Math.max(0, Math.min(window.innerHeight - 200, e.clientY - dragOffset.value.y))
  position.value = { x, y }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const toggleMinimize = () => {
  isMinimized.value = !isMinimized.value
}

// Display text
const displayText = computed(() => {
  if (!props.track) return 'No track'
  return `${props.track.artist || 'Unknown'} — ${props.track.title || 'Untitled'}`
})

const shouldMarquee = computed(() => displayText.value.length > 25)

// Cover
const coverStyle = computed(() => {
  if (props.track?.cover_url) return {}
  const str = props.track?.title || 'Music'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 40%) 0%, hsl(${(hue + 40) % 360}, 50%, 30%) 100%)`
  }
})

const coverInitials = computed(() => {
  const title = props.track?.title || 'M'
  return title.substring(0, 2).toUpperCase()
})

// Progress dots
const getDotClass = (index, total) => {
  const percent = (index / total) * 100
  const progressPercent = props.duration ? (props.progress / props.duration) * 100 : 0
  const bufferedPercent = props.duration ? (props.buffered / props.duration) * 100 : 0
  
  if (percent <= progressPercent) return 'active'
  if (percent <= bufferedPercent) return 'buffered'
  return ''
}

// Time format
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})
</script>

<style scoped>
.floating-player {
  position: fixed;
  z-index: 1000;
  background: #1a1a1a;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1);
  overflow: hidden;
  user-select: none;
  transition: box-shadow 0.2s, transform 0.2s;
}

.floating-player:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.15);
}

.floating-player.dragging {
  cursor: grabbing;
  transform: scale(1.02);
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.7);
}

.floating-player.minimized {
  width: 120px;
  height: 60px;
}

/* Drag handle */
.drag-handle {
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  background: rgba(255, 255, 255, 0.05);
}

.handle-dots {
  display: flex;
  gap: 3px;
}

.handle-dots span {
  width: 4px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
}

/* Minimized */
.minimized-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
}

.mini-cover {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
}

.mini-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-play-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #1DB954;
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* Full content */
.player-content {
  width: 280px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* LCD Screen */
.lcd-container {
  background: #111;
  border-radius: 8px;
  padding: 2px;
}

.lcd-screen {
  background: linear-gradient(180deg, #1a2a1a 0%, #0d1a0d 100%);
  border-radius: 6px;
  padding: 8px 10px;
  font-family: 'Courier New', monospace;
}

.lcd-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.lcd-row.main {
  margin-bottom: 4px;
}

.lcd-status {
  color: #33ff33;
  font-size: 10px;
  text-shadow: 0 0 4px #33ff33;
}

.lcd-title-wrap {
  flex: 1;
  overflow: hidden;
}

.lcd-title {
  color: #33ff33;
  font-size: 11px;
  white-space: nowrap;
  text-shadow: 0 0 4px #33ff33;
}

.lcd-title.marquee {
  display: flex;
  animation: lcd-scroll 10s linear infinite;
}

.lcd-title .clone {
  padding-left: 30px;
}

@keyframes lcd-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.lcd-row.sub {
  justify-content: space-between;
}

.lcd-time {
  color: #33ff33;
  font-size: 9px;
  opacity: 0.7;
}

.lcd-progress-dots {
  display: flex;
  gap: 2px;
}

.lcd-progress-dots .dot {
  width: 6px;
  height: 4px;
  background: rgba(51, 255, 51, 0.2);
  border-radius: 1px;
}

.lcd-progress-dots .dot.active {
  background: #33ff33;
  box-shadow: 0 0 3px #33ff33;
}

.lcd-progress-dots .dot.buffered {
  background: rgba(51, 255, 51, 0.4);
}

/* Cover */
.cover-section {
  display: flex;
  justify-content: center;
}

.cover-art {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: bold;
}

.cover-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  z-index: 1;
}

.vinyl-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.cover-art:hover .vinyl-overlay {
  opacity: 0.3;
}

.vinyl-overlay.spinning {
  opacity: 0.3;
  animation: vinyl-spin 3s linear infinite;
}

@keyframes vinyl-spin {
  to { transform: rotate(360deg); }
}

.vinyl-ring {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
}

.vinyl-ring:nth-child(1) {
  inset: 20%;
}

.vinyl-ring:nth-child(2) {
  inset: 35%;
}

.vinyl-center {
  position: absolute;
  inset: 45%;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
}

/* Controls */
.controls-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transport {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.ctrl-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.ctrl-btn:not(.play) {
  width: 36px;
  height: 36px;
}

.ctrl-btn.play {
  width: 48px;
  height: 48px;
  background: #1DB954;
}

.ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.ctrl-btn.play:hover {
  background: #1ed760;
}

.modes {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.mode-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s;
}

.mode-btn:hover {
  color: white;
}

.mode-btn.active {
  color: #1DB954;
}

/* Volume */
.volume-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
}

.vol-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 4px;
}

.vol-slider-wrap {
  flex: 1;
}

.vol-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  cursor: pointer;
}

.vol-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #1DB954;
  border-radius: 50%;
  cursor: pointer;
}

/* Expand button */
.expand-btn {
  position: absolute;
  top: 28px;
  right: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 4px;
  transition: all 0.15s;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

/* Spinner */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
