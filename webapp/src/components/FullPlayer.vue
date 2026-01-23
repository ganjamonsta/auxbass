<template>
  <div 
    class="full-player"
    ref="playerRef"
    @touchstart="onTouchStart"
    @touchmove="onTouchMove"
    @touchend="onTouchEnd"
    :style="swipeStyle"
  >
    <!-- Swipe indicator -->
    <div class="swipe-indicator"></div>

    <!-- Header -->
    <div class="player-header">
      <button class="close-btn" @click="$emit('close')">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
        </svg>
      </button>
      <span class="player-title">Сейчас играет</span>
      <button class="queue-btn" @click="showQueue = !showQueue">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
        </svg>
      </button>
    </div>

    <!-- Cover art with generated gradient -->
    <div class="player-cover" :class="{ swiping: isSwiping }">
      <div class="cover-image" :style="coverStyle">
        <span v-if="!track?.cover_url" class="cover-text">{{ coverInitials }}</span>
        <img v-else :src="track.cover_url" alt="Cover" class="cover-img" />
      </div>
      
      <!-- Swipe hint arrows -->
      <div v-if="isSwiping" class="swipe-arrows">
        <svg v-if="swipeDirection === 'left'" class="arrow left" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"/>
        </svg>
        <svg v-if="swipeDirection === 'right'" class="arrow right" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
        </svg>
      </div>
    </div>

    <!-- Track info -->
    <div class="player-info">
      <h2 class="track-title">{{ track?.title || 'Без названия' }}</h2>
      <p class="track-artist">{{ track?.artist || 'Неизвестный исполнитель' }}</p>
    </div>

    <!-- Progress bar -->
    <div class="progress-container">
      <input 
        type="range"
        class="progress-slider"
        :value="progress"
        :max="duration || 100"
        @input="$emit('seek', Number($event.target.value))"
      />
      <div class="progress-times">
        <span>{{ formatTime(progress) }}</span>
        <span>{{ formatTime(duration) }}</span>
      </div>
    </div>

    <!-- Controls -->
    <div class="player-controls">
      <button 
        class="control-btn secondary"
        :class="{ active: shuffle }"
        @click="$emit('toggleShuffle')"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
        </svg>
      </button>
      
      <button class="control-btn" @click="$emit('prev')">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
        </svg>
      </button>
      
      <button class="control-btn play-btn" @click="$emit('toggle')">
        <!-- Loading spinner -->
        <svg v-if="loading" class="spinner" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10" stroke-width="2" stroke-opacity="0.3"/>
          <path d="M12 2a10 10 0 0 1 10 10" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <svg v-else-if="isPlaying" width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
        </svg>
        <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </button>
      
      <button class="control-btn" @click="$emit('next')">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
        </svg>
      </button>
      
      <button 
        class="control-btn secondary"
        :class="{ active: repeat !== 'none' }"
        @click="$emit('toggleRepeat')"
      >
        <svg v-if="repeat === 'one'" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
        </svg>
        <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
        </svg>
      </button>
    </div>

    <!-- Volume control -->
    <div class="volume-container">
      <button class="volume-btn" @click="$emit('toggleMute')">
        <svg v-if="isMuted || volume === 0" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
        </svg>
        <svg v-else-if="volume < 0.5" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>
        </svg>
        <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
      </button>
      <input 
        type="range"
        class="volume-slider"
        :value="isMuted ? 0 : volume * 100"
        min="0"
        max="100"
        @input="$emit('setVolume', Number($event.target.value) / 100)"
      />
    </div>

    <!-- Mini queue -->
    <Transition name="slide-up-queue">
      <div v-if="showQueue" class="mini-queue">
        <div class="queue-header">
          <span>Очередь</span>
          <button @click="showQueue = false" class="close-queue">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>
        <div class="queue-list">
          <div 
            v-for="(t, idx) in upcomingQueue" 
            :key="`q-${idx}`"
            class="queue-item"
          >
            <span class="queue-num">{{ idx + 1 }}</span>
            <div class="queue-info">
              <span class="queue-title">{{ t.title || 'Без названия' }}</span>
              <span class="queue-artist">{{ t.artist || 'Неизвестный' }}</span>
            </div>
          </div>
          <div v-if="!upcomingQueue.length" class="queue-empty">
            Нет треков в очереди
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'

const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  loading: {
    type: Boolean,
    default: false
  },
  progress: Number,
  duration: Number,
  volume: {
    type: Number,
    default: 1
  },
  isMuted: {
    type: Boolean,
    default: false
  },
  shuffle: Boolean,
  repeat: String,
  queue: {
    type: Array,
    default: () => []
  },
  queueIndex: {
    type: Number,
    default: -1
  }
})

const emit = defineEmits([
  'close',
  'toggle',
  'next',
  'prev',
  'seek',
  'setVolume',
  'toggleMute',
  'toggleShuffle',
  'toggleRepeat',
])

const telegram = inject('telegram')

// Swipe handling
const playerRef = ref(null)
const touchStart = ref({ x: 0, y: 0 })
const touchCurrent = ref({ x: 0, y: 0 })
const isSwiping = ref(false)
const swipeDirection = ref(null)
const showQueue = ref(false)

const SWIPE_THRESHOLD = 80

const onTouchStart = (e) => {
  const touch = e.touches[0]
  touchStart.value = { x: touch.clientX, y: touch.clientY }
  touchCurrent.value = { x: touch.clientX, y: touch.clientY }
  isSwiping.value = false
  swipeDirection.value = null
}

const onTouchMove = (e) => {
  const touch = e.touches[0]
  touchCurrent.value = { x: touch.clientX, y: touch.clientY }
  
  const deltaX = touchCurrent.value.x - touchStart.value.x
  const deltaY = touchCurrent.value.y - touchStart.value.y
  
  // Determine swipe direction
  if (Math.abs(deltaX) > 20 || Math.abs(deltaY) > 20) {
    isSwiping.value = true
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      swipeDirection.value = deltaX > 0 ? 'right' : 'left'
    } else {
      swipeDirection.value = deltaY > 0 ? 'down' : 'up'
    }
  }
}

const onTouchEnd = () => {
  const deltaX = touchCurrent.value.x - touchStart.value.x
  const deltaY = touchCurrent.value.y - touchStart.value.y
  
  // Swipe down to close
  if (deltaY > SWIPE_THRESHOLD && Math.abs(deltaY) > Math.abs(deltaX)) {
    telegram?.HapticFeedback?.impactOccurred?.('light')
    emit('close')
  }
  // Swipe left for next
  else if (deltaX < -SWIPE_THRESHOLD && Math.abs(deltaX) > Math.abs(deltaY)) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('next')
  }
  // Swipe right for prev
  else if (deltaX > SWIPE_THRESHOLD && Math.abs(deltaX) > Math.abs(deltaY)) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('prev')
  }
  
  isSwiping.value = false
  swipeDirection.value = null
  touchStart.value = { x: 0, y: 0 }
  touchCurrent.value = { x: 0, y: 0 }
}

const swipeStyle = computed(() => {
  if (!isSwiping.value) return {}
  
  const deltaX = touchCurrent.value.x - touchStart.value.x
  const deltaY = touchCurrent.value.y - touchStart.value.y
  
  // Only apply transform for down swipe
  if (swipeDirection.value === 'down' && deltaY > 0) {
    return {
      transform: `translateY(${Math.min(deltaY * 0.5, 100)}px)`,
      opacity: 1 - (deltaY / 400)
    }
  }
  
  return {}
})

// Generate cover from title
const coverGradient = computed(() => {
  const title = props.track?.title || 'Music'
  const artist = props.track?.artist || ''
  
  // Generate colors from string hash
  const str = title + artist
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  
  return `linear-gradient(135deg, hsl(${hue1}, 70%, 35%) 0%, hsl(${hue2}, 60%, 25%) 100%)`
})

const coverStyle = computed(() => {
  if (props.track?.cover_url) {
    return {}
  }
  return {
    background: coverGradient.value
  }
})

const coverInitials = computed(() => {
  const title = props.track?.title || 'M'
  const words = title.split(' ').filter(w => w.length > 0)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }
  return title.substring(0, 2).toUpperCase()
})

const upcomingQueue = computed(() => {
  if (!props.queue.length || props.queueIndex < 0) return []
  return props.queue.slice(props.queueIndex + 1, props.queueIndex + 6)
})

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.full-player {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, var(--spotify-gray-dark) 0%, var(--spotify-black) 40%);
  display: flex;
  flex-direction: column;
  z-index: 100;
  padding: 12px 24px 24px;
  transition: transform 0.1s ease-out, opacity 0.1s ease-out;
  touch-action: pan-y;
}

/* Swipe indicator */
.swipe-indicator {
  width: 40px;
  height: 4px;
  background: var(--spotify-gray-light);
  border-radius: 2px;
  margin: 0 auto 12px;
}

.player-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.close-btn, .queue-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--spotify-text);
  opacity: 0.7;
  transition: opacity 0.2s;
}

.close-btn:active, .queue-btn:active {
  opacity: 1;
}

.player-title {
  flex: 1;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--spotify-text-secondary);
}

.player-cover {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  max-height: 320px;
  margin-bottom: 24px;
}

.cover-image {
  width: 100%;
  max-width: 300px;
  aspect-ratio: 1;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  transition: transform 0.2s;
}

.player-cover.swiping .cover-image {
  transform: scale(0.95);
}

.cover-text {
  font-size: 72px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Swipe arrows */
.swipe-arrows {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.arrow {
  position: absolute;
  color: var(--spotify-green);
  opacity: 0.8;
  animation: pulse 0.5s ease infinite;
}

.arrow.left {
  left: 10%;
}

.arrow.right {
  right: 10%;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; }
}

.player-info {
  text-align: center;
  margin-bottom: 24px;
}

.track-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-artist {
  font-size: 15px;
  color: var(--spotify-text-secondary);
}

.progress-container {
  margin-bottom: 20px;
}

.progress-slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--spotify-gray);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--spotify-text);
  cursor: pointer;
  transition: transform 0.1s;
}

.progress-slider:active::-webkit-slider-thumb {
  transform: scale(1.2);
}

.progress-times {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: var(--spotify-text-muted);
}

.player-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 24px;
}

.control-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text);
  transition: transform 0.1s, opacity 0.2s;
}

.control-btn:active {
  transform: scale(0.95);
}

.control-btn.secondary {
  width: 40px;
  height: 40px;
  color: var(--spotify-text-muted);
}

.control-btn.secondary.active {
  color: var(--spotify-green);
}

.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--spotify-text);
  color: var(--spotify-black);
}

.play-btn:active {
  background: var(--spotify-text-secondary);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.volume-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.volume-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-muted);
}

.volume-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--spotify-gray);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--spotify-text);
  cursor: pointer;
}

/* Mini queue */
.mini-queue {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--spotify-gray);
  border-radius: 16px 16px 0 0;
  padding: 16px;
  max-height: 50%;
  overflow-y: auto;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.close-queue {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--spotify-text-muted);
  cursor: pointer;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--spotify-gray-dark);
}

.queue-num {
  width: 24px;
  text-align: center;
  font-size: 14px;
  color: var(--spotify-text-muted);
}

.queue-info {
  flex: 1;
  min-width: 0;
}

.queue-title {
  display: block;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-artist {
  display: block;
  font-size: 12px;
  color: var(--spotify-text-muted);
}

.queue-empty {
  text-align: center;
  color: var(--spotify-text-muted);
  padding: 20px;
}

/* Queue animation */
.slide-up-queue-enter-active,
.slide-up-queue-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-queue-enter-from,
.slide-up-queue-leave-to {
  transform: translateY(100%);
}
</style>
