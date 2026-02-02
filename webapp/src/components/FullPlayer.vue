<template>
  <div 
    class="full-player"
    ref="playerRef"
  >
    <!-- Tap indicator to minimize -->
    <div class="swipe-indicator" @click="$emit('close')"></div>

    <!-- Header -->
    <div class="player-header">
      <button class="close-btn" @click="$emit('close')">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
        </svg>
      </button>
      <span class="player-title">Сейчас играет</span>
      <button class="menu-btn" @click="openTrackContextMenu" title="Меню трека">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
        </svg>
      </button>
    </div>

    <!-- Cover art with generated gradient - swipe area for track navigation -->
    <div 
      class="player-cover" 
      :class="{ swiping: isSwiping }"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <div class="cover-image" :style="coverStyle">
        <span v-if="!track?.cover_url" class="cover-text">{{ coverInitials }}</span>
        <img v-else :src="track.cover_url" alt="Cover" class="cover-img" />
      </div>

      <!-- Loading Overlay -->
      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" stroke-width="4" stroke-opacity="0.3"/>
            <path d="M12 2a10 10 0 0 1 10 10" stroke-width="4" stroke-linecap="round"/>
          </svg>
        </div>
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
      <div class="track-info-row">
        <h2 class="track-title">{{ getDisplayTitle(track) }}</h2>
        <!-- HD indicator badge -->
        <span v-if="playerStore.hdTrackInfo" class="hd-badge" title="HD версия доступна для скачивания">
          HD
        </span>
        <button 
          class="like-btn" 
          :class="{ liked: isLiked }" 
          @click="$emit('like')"
          title="Лайк"
        >
          <svg v-if="isLiked" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
          </svg>
        </button>
      </div>
      <p class="track-artist">
        <template v-if="parsedArtists.length > 0">
          <template v-for="(artist, index) in parsedArtists" :key="artist">
            <span 
              class="artist-link"
              @click="goToArtist(artist)"
            >{{ artist }}</span>
            <span v-if="index < parsedArtists.length - 1" class="artist-sep">, </span>
          </template>
        </template>
        <span v-else>{{ getDisplayArtist(track) }}</span>
      </p>
    </div>

    <!-- Progress bar -->
    <div class="progress-container">
      <div class="slider-wrapper">
        <div class="buffered-bar" :style="{ width: (buffered / (duration || 1)) * 100 + '%' }"></div>
        <input 
          type="range"
          class="progress-slider"
          :value="progress"
          :max="duration || 100"
          @input="$emit('seek', Number($event.target.value))"
        />
      </div>
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

    <!-- Bottom controls: Volume + Queue -->
    <div class="bottom-controls">
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
      <button 
        class="queue-toggle-btn" 
        :class="{ active: showQueue }"
        @click="showQueue = !showQueue"
        title="Очередь"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
        </svg>
      </button>
    </div>

    <!-- Mini queue -->
    <Transition name="slide-up-queue">
      <div v-if="showQueue" class="mini-queue">
        <div class="queue-header">
          <span>Очередь</span>
          <span class="queue-hint">← свайп для удаления</span>
          <button @click="showQueue = false" class="close-queue">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
            </svg>
          </button>
        </div>
        <div class="queue-list" ref="queueListRef">
          <div 
            v-for="(t, idx) in upcomingQueue" 
            :key="`q-${t.id}-${idx}`"
            class="queue-item"
            :class="{ 
              swiping: swipingQueueIndex === idx,
              'swipe-delete': swipeDeleteProgress > 0.5 && swipingQueueIndex === idx,
              dragging: draggingIndex === idx,
              'drag-over': dragOverIndex === idx && draggingIndex !== idx
            }"
            :style="getQueueItemStyle(idx)"
            draggable="true"
            @dragstart="onDragStart($event, idx)"
            @dragover="onDragOver($event, idx)"
            @dragend="onDragEnd"
            @drop="onDrop($event, idx)"
            @touchstart="onQueueTouchStart($event, idx)"
            @touchmove="onQueueTouchMove($event, idx)"
            @touchend="onQueueTouchEnd($event, idx)"
            @click="$emit('playFromQueue', idx)"
            @contextmenu.prevent="openMenu('track', t, 'queue', $event)"
          >
            <div class="drag-handle">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
              </svg>
            </div>
            <span class="queue-num">{{ idx + 1 }}</span>
            <div class="queue-info">
              <span class="queue-title">{{ getDisplayTitle(t) }}</span>
              <span class="queue-artist">{{ getDisplayArtist(t) }}</span>
            </div>
            <div class="delete-indicator">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
            </div>
          </div>
          <div v-if="lazyShuffleMode" class="queue-lazy-shuffle">
            <div class="lazy-shuffle-icon">🔀</div>
            <div class="lazy-shuffle-info">
              <span class="lazy-shuffle-title">Режим перемешивания</span>
              <span class="lazy-shuffle-meta">{{ lazyShuffleIndex + 1 }} из {{ lazyShuffleTotal }} треков</span>
            </div>
          </div>
          <div v-else-if="!upcomingQueue.length" class="queue-empty">
            Нет треков в очереди
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { getTrackCoverStyle, getTrackInitials, splitArtists, getDisplayTitle, getDisplayArtist } from '@/utils'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useContextMenu } from '@/composables/useContextMenu'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  loading: {
    type: Boolean,
    default: false
  },
  progress: Number,
  duration: Number,
  buffered: {
    type: Number,
    default: 0
  },
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
  },
  isLiked: {
    type: Boolean,
    default: false
  },
  lazyShuffleMode: {
    type: Boolean,
    default: false
  },
  lazyShuffleTotal: {
    type: Number,
    default: 0
  },
  lazyShuffleIndex: {
    type: Number,
    default: -1
  },
  shuffleOrder: {
    type: Array,
    default: () => []
  },
  shuffleIndex: {
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
  'removeFromQueue',
  'moveInQueue',
  'playFromQueue',
  'like',
])

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const { openMenu } = useContextMenu()

const telegram = inject('telegram')

// Parse artists into separate names
const parsedArtists = computed(() => {
  if (!props.track?.artist) return []
  return splitArtists(props.track.artist)
})

// Navigate to artist page
const goToArtist = (artistName) => {
  if (artistName) {
    router.push(`/artist/${encodeURIComponent(artistName)}`)
    emit('close')
  }
}

// Open track context menu (uses unified context menu)
const openTrackContextMenu = () => {
  telegram?.HapticFeedback?.impactOccurred?.('light')
  openMenu('track', props.track, 'player')
}

// Swipe handling for cover
const playerRef = ref(null)
const touchStart = ref({ x: 0, y: 0 })
const touchCurrent = ref({ x: 0, y: 0 })
const isSwiping = ref(false)
const swipeDirection = ref(null)
const showQueue = ref(false)

// Queue interaction state
const queueListRef = ref(null)
const swipingQueueIndex = ref(-1)
const swipeStartX = ref(0)
const swipeCurrentX = ref(0)
const swipeDeleteProgress = ref(0)
const draggingIndex = ref(-1)
const dragOverIndex = ref(-1)

const SWIPE_THRESHOLD = 80
const QUEUE_SWIPE_DELETE_THRESHOLD = 100

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
  
  // Only handle horizontal swipes for track navigation
  if (Math.abs(deltaX) > 20 && Math.abs(deltaX) > Math.abs(deltaY)) {
    isSwiping.value = true
    swipeDirection.value = deltaX > 0 ? 'right' : 'left'
  }
}

const onTouchEnd = () => {
  const deltaX = touchCurrent.value.x - touchStart.value.x
  const deltaY = touchCurrent.value.y - touchStart.value.y
  
  // Only handle horizontal swipes (left/right for track navigation)
  // Swipe left for next
  if (deltaX < -SWIPE_THRESHOLD && Math.abs(deltaX) > Math.abs(deltaY)) {
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

// Swipe style removed - no longer using swipe-down gesture
// to avoid conflict with Telegram's native close gesture

// Use shared utils for cover style
const coverStyle = computed(() => getTrackCoverStyle(props.track))
const coverInitials = computed(() => getTrackInitials(props.track))

const upcomingQueue = computed(() => {
  if (!props.queue.length || props.queueIndex < 0) return []
  
  // If shuffle mode with shuffleOrder, show tracks in shuffle order
  if (props.shuffle && props.shuffleOrder.length > 0 && props.shuffleIndex >= 0) {
    const upcoming = []
    for (let i = 1; i <= 5; i++) {
      const nextShuffleIdx = props.shuffleIndex + i
      if (nextShuffleIdx >= props.shuffleOrder.length) break
      const queueIdx = props.shuffleOrder[nextShuffleIdx]
      if (props.queue[queueIdx]) {
        upcoming.push(props.queue[queueIdx])
      }
    }
    return upcoming
  }
  
  // Normal mode - show next tracks in order
  return props.queue.slice(props.queueIndex + 1, props.queueIndex + 6)
})

// Queue item swipe handling (for touch devices)
const onQueueTouchStart = (e, idx) => {
  swipingQueueIndex.value = idx
  swipeStartX.value = e.touches[0].clientX
  swipeCurrentX.value = e.touches[0].clientX
  swipeDeleteProgress.value = 0
}

const onQueueTouchMove = (e, idx) => {
  if (swipingQueueIndex.value !== idx) return
  
  swipeCurrentX.value = e.touches[0].clientX
  const deltaX = swipeStartX.value - swipeCurrentX.value
  
  // Only allow left swipe (positive deltaX)
  if (deltaX > 0) {
    e.preventDefault()
    swipeDeleteProgress.value = Math.min(1, deltaX / QUEUE_SWIPE_DELETE_THRESHOLD)
  }
}

const onQueueTouchEnd = (e, idx) => {
  if (swipingQueueIndex.value !== idx) return
  
  const deltaX = swipeStartX.value - swipeCurrentX.value
  
  if (deltaX > QUEUE_SWIPE_DELETE_THRESHOLD) {
    // Delete the item
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('removeFromQueue', idx)
  }
  
  // Reset state
  swipingQueueIndex.value = -1
  swipeStartX.value = 0
  swipeCurrentX.value = 0
  swipeDeleteProgress.value = 0
}

const getQueueItemStyle = (idx) => {
  if (swipingQueueIndex.value === idx && swipeDeleteProgress.value > 0) {
    const translateX = -(swipeDeleteProgress.value * QUEUE_SWIPE_DELETE_THRESHOLD)
    return {
      transform: `translateX(${translateX}px)`,
      transition: 'none'
    }
  }
  return {}
}

// Drag and drop for reordering
const onDragStart = (e, idx) => {
  draggingIndex.value = idx
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', idx.toString())
}

const onDragOver = (e, idx) => {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  dragOverIndex.value = idx
}

const onDragEnd = () => {
  draggingIndex.value = -1
  dragOverIndex.value = -1
}

const onDrop = (e, toIdx) => {
  e.preventDefault()
  const fromIdx = parseInt(e.dataTransfer.getData('text/plain'))
  
  if (fromIdx !== toIdx) {
    telegram?.HapticFeedback?.impactOccurred?.('light')
    emit('moveInQueue', fromIdx, toIdx)
  }
  
  draggingIndex.value = -1
  dragOverIndex.value = -1
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 FULL PLAYER - Nokia XpressMusic Neumorphic Style
   Main player interface with large cover and controls
   ═══════════════════════════════════════════════════════════ */

.full-player {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, var(--xm-bg-elevated) 0%, var(--xm-bg-deep) 50%);
  display: flex;
  flex-direction: column;
  z-index: 100;
  padding: 8px 16px;
  padding-bottom: max(16px, env(safe-area-inset-bottom, 16px));
  transition: transform 0.1s ease-out, opacity 0.1s ease-out;
  touch-action: pan-y;
  overflow: hidden;
}

/* ─── Swipe Indicator ─── */
.swipe-indicator {
  width: 40px;
  height: 5px;
  background: var(--xm-bg-hover);
  border-radius: var(--neu-radius-full);
  margin: 0 auto 8px;
  flex-shrink: 0;
  cursor: pointer;
  padding: 8px 40px;
  background-clip: content-box;
  transition: background-color 0.2s;
}

.swipe-indicator:hover {
  background-color: var(--xm-text-secondary);
}

.swipe-indicator:active {
  background-color: var(--xm-accent);
}

/* ─── Header ─── */
.player-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.close-btn, .menu-btn {
  width: 44px;
  height: 44px;
  border: none;
  background: var(--xm-bg-surface);
  border-radius: var(--neu-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--xm-text-primary);
  opacity: 0.8;
  transition: all 0.2s ease;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.close-btn:active, .menu-btn:active {
  opacity: 1;
  transform: scale(0.95);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.player-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--xm-text-secondary);
}

/* ─── Cover Art ─── */
.player-cover {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 0;
  margin-bottom: 20px;
}

.cover-image {
  width: 100%;
  max-width: min(300px, 38vh);
  aspect-ratio: 1;
  border-radius: var(--neu-radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    16px 16px 32px var(--neu-shadow-dark),
    -8px -8px 16px var(--neu-shadow-light),
    0 0 60px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  transition: transform 0.2s ease;
  border: 2px solid rgba(255, 255, 255, 0.04);
  position: relative;
}

/* Vinyl record effect behind cover */
.cover-image::before {
  content: '';
  position: absolute;
  inset: -10%;
  background: conic-gradient(
    from 0deg,
    rgba(30, 30, 30, 0.8) 0deg,
    rgba(50, 50, 50, 0.8) 90deg,
    rgba(30, 30, 30, 0.8) 180deg,
    rgba(50, 50, 50, 0.8) 270deg,
    rgba(30, 30, 30, 0.8) 360deg
  );
  border-radius: 50%;
  z-index: -1;
  opacity: 0.3;
}

.player-cover.swiping .cover-image {
  transform: scale(0.93);
}

.cover-text {
  font-size: 72px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.6);
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ─── Swipe Arrows ─── */
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
  color: var(--xm-accent);
  opacity: 0.9;
  animation: pulse 0.5s ease infinite;
  filter: drop-shadow(0 0 8px var(--xm-accent-glow));
}

.arrow.left {
  left: 8%;
}

.arrow.right {
  right: 8%;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* ─── Track Info ─── */
.player-info {
  text-align: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.track-info-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 6px;
}

.track-title {
  font-size: 22px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
}

.like-btn {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border: none;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  transition: all 0.2s ease;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

/* HD Badge - shows when HD version is available */
.hd-badge {
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #1a1a2e;
  border-radius: 4px;
  margin-left: 8px;
  flex-shrink: 0;
  animation: hd-badge-pulse 2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.5);
}

@keyframes hd-badge-pulse {
  0%, 100% { 
    box-shadow: 0 0 8px rgba(255, 215, 0, 0.5);
  }
  50% { 
    box-shadow: 0 0 16px rgba(255, 215, 0, 0.8);
  }
}

.like-btn:active {
  transform: scale(0.9);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 2px var(--neu-shadow-inset-light);
}

.like-btn.liked {
  color: #ff4b7b;
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 2px var(--neu-shadow-inset-light),
    0 0 12px rgba(255, 75, 123, 0.4);
}

.like-btn.liked svg {
  filter: drop-shadow(0 0 6px rgba(255, 75, 123, 0.6));
}

.track-artist {
  font-size: 15px;
  color: var(--xm-text-secondary);
}

.track-artist .artist-link {
  cursor: pointer;
  transition: color 0.2s ease;
}

.track-artist .artist-link:hover {
  color: #1DB954;
  text-decoration: underline;
}

.track-artist .artist-sep {
  color: var(--xm-text-secondary);
  opacity: 0.6;
}

/* ─── Progress Bar ─── */
.progress-container {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.slider-wrapper {
  position: relative;
  width: 100%;
  height: 8px;
  border-radius: var(--neu-radius-full);
  background: var(--xm-bg-surface);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
}

.buffered-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--neu-radius-full);
  z-index: 1;
  pointer-events: none;
  transition: width 0.2s linear;
}

.progress-slider {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  border-radius: var(--neu-radius-full);
  outline: none;
  cursor: pointer;
  z-index: 2;
  margin: 0;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: var(--neu-radius-full);
  background: linear-gradient(145deg, var(--xm-accent-light), var(--xm-accent));
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light),
    0 0 12px var(--xm-accent-glow);
}

.progress-slider:active::-webkit-slider-thumb {
  transform: scale(1.2);
}

.progress-times {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--xm-text-muted);
  font-variant-numeric: tabular-nums;
}

/* ─── Main Controls ─── */
.player-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.control-btn {
  width: 52px;
  height: 52px;
  border: none;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-primary);
  transition: all 0.15s ease;
  box-shadow: 
    5px 5px 10px var(--neu-shadow-dark),
    -3px -3px 6px var(--neu-shadow-light);
}

.control-btn:active {
  transform: scale(0.93);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light);
}

.control-btn.secondary {
  width: 44px;
  height: 44px;
  color: var(--xm-text-muted);
}

.control-btn.secondary.active {
  color: var(--xm-accent);
  box-shadow: 
    inset 3px 3px 6px var(--neu-shadow-inset-dark),
    inset -2px -2px 4px var(--neu-shadow-inset-light),
    0 0 16px var(--xm-accent-glow);
}

/* ─── Play Button (Main action) ─── */
.play-btn {
  width: 72px;
  height: 72px;
  border-radius: var(--neu-radius-full);
  background: linear-gradient(145deg, var(--xm-accent-light), var(--xm-accent-dark));
  color: white;
  box-shadow: 
    8px 8px 16px var(--neu-shadow-dark),
    -4px -4px 10px var(--neu-shadow-light),
    0 0 30px var(--xm-accent-glow);
}

.play-btn:active {
  transform: scale(0.93);
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.4),
    0 0 20px var(--xm-accent-glow);
}

/* ─── Loading Overlay ─── */
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 5;
  border-radius: var(--neu-radius-xl);
}

.loading-spinner {
  color: var(--xm-accent);
  animation: spin 1s linear infinite;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ─── Bottom Controls ─── */
.bottom-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 8px;
  margin-top: auto;
  flex-shrink: 0;
}

.volume-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.queue-toggle-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--neu-radius-full);
  background: var(--xm-bg-surface);
  border: none;
  color: var(--xm-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  box-shadow: 
    4px 4px 8px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.queue-toggle-btn:active {
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.queue-toggle-btn.active {
  color: var(--xm-accent);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light),
    0 0 12px var(--xm-accent-glow);
}

.volume-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  transition: color 0.15s ease;
}

.volume-btn:active {
  color: var(--xm-accent);
}

.volume-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--xm-bg-surface);
  border-radius: var(--neu-radius-full);
  outline: none;
  cursor: pointer;
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: var(--neu-radius-full);
  background: var(--xm-text-primary);
  cursor: pointer;
  box-shadow: 
    2px 2px 5px var(--neu-shadow-dark),
    -1px -1px 3px var(--neu-shadow-light);
  transition: transform 0.1s ease;
}

.volume-slider:active::-webkit-slider-thumb {
  transform: scale(1.15);
}

/* ─── Mini Queue Panel ─── */
.mini-queue {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--xm-bg-elevated);
  border-radius: var(--neu-radius-xl) var(--neu-radius-xl) 0 0;
  padding: 20px;
  padding-bottom: max(24px, env(safe-area-inset-bottom, 24px));
  max-height: 55%;
  overflow-y: overlay;
  overflow-x: hidden;
  scrollbar-gutter: auto;
  z-index: 200;
  box-shadow: 
    0 -10px 30px var(--neu-shadow-dark),
    0 -4px 12px var(--neu-shadow-light);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-bottom: none;
}

.mini-queue::-webkit-scrollbar {
  width: 6px;
  background: transparent;
}

.mini-queue::-webkit-scrollbar-track {
  background: transparent;
}

.mini-queue::-webkit-scrollbar-thumb {
  background: var(--xm-accent);
  border-radius: 3px;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 700;
  font-size: 16px;
  color: var(--xm-text-primary);
}

.queue-hint {
  font-size: 11px;
  color: var(--xm-text-muted);
  font-weight: 400;
}

.close-queue {
  width: 36px;
  height: 36px;
  border: none;
  background: var(--xm-bg-surface);
  border-radius: var(--neu-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: pointer;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
  transition: all 0.15s ease;
}

.close-queue:active {
  transform: scale(0.95);
  box-shadow: 
    inset 2px 2px 4px var(--neu-shadow-inset-dark),
    inset -1px -1px 3px var(--neu-shadow-inset-light);
}

.queue-list {
  overflow: hidden;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 10px;
  border-radius: var(--neu-radius-md);
  margin-bottom: 8px;
  cursor: pointer;
  position: relative;
  background: var(--xm-bg-surface);
  transition: transform 0.2s ease, background 0.2s ease;
  user-select: none;
  touch-action: pan-y;
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light);
}

.queue-item:active {
  background: var(--xm-bg-hover);
  transform: scale(0.98);
}

.queue-item.swiping {
  transition: none;
}

.queue-item.swipe-delete {
  background: rgba(229, 57, 53, 0.2);
  box-shadow: 
    3px 3px 6px var(--neu-shadow-dark),
    -2px -2px 4px var(--neu-shadow-light),
    0 0 12px rgba(229, 57, 53, 0.3);
}

.queue-item.dragging {
  opacity: 0.5;
  background: var(--xm-bg-hover);
}

.queue-item.drag-over {
  border-top: 2px solid var(--xm-accent);
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-text-muted);
  cursor: grab;
  padding: 4px;
  flex-shrink: 0;
}

.drag-handle:active {
  cursor: grabbing;
  color: var(--xm-accent);
}

.queue-num {
  width: 22px;
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--xm-accent);
  flex-shrink: 0;
}

.queue-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.queue-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--xm-text-primary);
}

.queue-artist {
  display: block;
  font-size: 12px;
  color: var(--xm-text-muted);
}

.delete-indicator {
  position: absolute;
  right: -40px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--xm-accent);
  opacity: 0;
  transition: opacity 0.2s;
}

.queue-item.swiping .delete-indicator {
  opacity: 1;
  right: 8px;
}

.queue-empty {
  text-align: center;
  color: var(--xm-text-muted);
  padding: 24px;
  font-size: 14px;
}

.queue-lazy-shuffle {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--xm-surface-alpha);
  border-radius: 12px;
  margin: 8px 0;
}

.lazy-shuffle-icon {
  font-size: 24px;
}

.lazy-shuffle-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lazy-shuffle-title {
  font-weight: 600;
  color: var(--xm-text-primary);
  font-size: 14px;
}

.lazy-shuffle-meta {
  color: var(--xm-text-muted);
  font-size: 12px;
}

/* ─── Queue Animation ─── */
.slide-up-queue-enter-active,
.slide-up-queue-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-queue-enter-from,
.slide-up-queue-leave-to {
  transform: translateY(100%);
}
</style>
