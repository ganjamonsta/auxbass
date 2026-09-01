<template>
  <div
    v-if="track"
    class="player-sheet"
    :class="sheetClasses"
    :style="sheetStyle"
  >
    <!-- Backdrop overlay -->
    <div
      class="sheet-backdrop"
      @click="collapse"
    />

    <!-- Sheet container (holds header + body) -->
    <div class="sheet-container">
      <!-- Header: Mini-player that transforms into compact bar -->
      <div
        class="sheet-header"
        ref="headerRef"
        @click="handleHeaderTap"
        @touchstart.passive="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
        @touchcancel="onTouchEnd"
        @contextmenu.prevent="openTrackContextMenu"
      >
        <!-- Drag handle pill -->
        <div class="sheet-drag-handle">
          <div class="drag-pill" />
        </div>

        <!-- COLLAPSED STATE: LCD Nokia-style mini player -->
        <div class="header-collapsed">
          <div class="lcd-screen">
            <!-- Row 1: Title + Indicators -->
            <div class="lcd-row row-title">
              <div class="lcd-title-container">
                <div class="lcd-title-track" :class="{ 'marquee': shouldMarquee }">
                  <span class="lcd-title">{{ displayText }}</span>
                  <span v-if="shouldMarquee" class="lcd-title lcd-title-clone">{{ displayText }}</span>
                </div>
              </div>
              <div class="lcd-indicators">
                <span
                  v-if="networkMonitor.hasIssues.value"
                  class="lcd-indicator net-indicator active"
                  :class="{ pulse: networkMonitor.connectionState.value === 'reconnecting' }"
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
                <span v-if="playerStore.hdTrackInfo" class="lcd-indicator hd-indicator active" title="HD">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
                  </svg>
                </span>
                <span v-else class="lcd-indicator hd-indicator">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8 12H9.5v-2h-2v2H6V9h1.5v2.5h2V9H11v6zm2-6h4c.55 0 1 .45 1 1v4c0 .55-.45 1-1 1h-4V9zm1.5 4.5h2v-3h-2v3z"/>
                  </svg>
                </span>
                <span
                  class="lcd-indicator like-indicator"
                  :class="{ active: isLiked }"
                  @click.stop="$emit('like')"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" :fill="isLiked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                  </svg>
                </span>
                <span
                  class="lcd-indicator shuffle-indicator"
                  :class="{ active: shuffle }"
                  @click.stop="$emit('toggleShuffle')"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
                  </svg>
                </span>
                <span
                  class="lcd-indicator repeat-indicator"
                  :class="{ active: repeat !== 'none' }"
                  @click.stop="$emit('toggleRepeat')"
                >
                  <svg v-if="repeat === 'one'" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4zm-4-2V9h-1l-2 1v1h1.5v4H13z"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
                  </svg>
                </span>
              </div>
            </div>
            <!-- Row 2: Progress + Time + Buttons -->
            <div class="lcd-row row-controls">
              <div class="lcd-progress">
                <span
                  class="lcd-dot"
                  v-for="i in 20"
                  :key="i"
                  :class="getDotClass(i, 20)"
                />
              </div>
              <span class="lcd-time">{{ formatTime(progress) }}/{{ formatTime(duration || track.duration) }}</span>
              <div class="lcd-buttons">
                <button class="lcd-btn" @click.stop="$emit('toggle')" title="Play/Pause">
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
                <button class="lcd-btn" @click.stop="$emit('next')" title="Next">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- EXPANDED STATE: Compact bar with cover thumbnail + title -->
        <div class="header-expanded">
          <button class="collapse-btn" @click.stop="collapse" title="Свернуть">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
            </svg>
          </button>
          <div class="expanded-cover" :style="coverThumbStyle">
            <img v-if="track?.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.SM)" alt="" class="cover-thumb-img" />
            <span v-else class="cover-thumb-text">{{ coverInitials }}</span>
          </div>
          <div class="expanded-info">
            <span class="expanded-title">{{ getDisplayTitle(track) }}</span>
            <span class="expanded-artist">{{ getDisplayArtist(track) }}</span>
          </div>
          <span class="expanded-time">{{ formatTime(progress) }}</span>
        </div>
      </div>

      <!-- Body: Fullscreen player content -->
      <div class="sheet-body" ref="bodyRef">
        <!-- Cover art with swipe prev/next -->
        <div
          class="body-cover"
          :class="{ swiping: isCoverSwiping }"
          @touchstart.passive="onCoverTouchStart"
          @touchmove="onCoverTouchMove"
          @touchend="onCoverTouchEnd"
          @touchcancel="onCoverTouchEnd"
          @contextmenu.prevent="openTrackContextMenu"
        >
          <div class="cover-image" :style="coverStyle">
            <img v-if="track?.cover_url" :src="getCoverUrl(track.cover_url, CoverSize.XL)" alt="Cover" class="cover-img" />
            <span v-else class="cover-text">{{ coverInitials }}</span>
          </div>
          <!-- Loading overlay -->
          <div v-if="loading" class="loading-overlay">
            <div class="loading-spinner">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="4" stroke-opacity="0.3"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke-width="4" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
          <!-- Swipe arrows -->
          <div v-if="isCoverSwiping" class="swipe-arrows">
            <svg v-if="coverSwipeDir === 'left'" class="arrow left" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6 1.41-1.41z"/>
            </svg>
            <svg v-if="coverSwipeDir === 'right'" class="arrow right" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
            </svg>
          </div>
        </div>

        <!-- Track info -->
        <div class="body-info" @contextmenu.prevent="openTrackContextMenu">
          <div class="track-info-row">
            <h2 class="track-title">{{ getDisplayTitle(track) }}</h2>
            <span v-if="playerStore.hdTrackInfo" class="hd-badge" title="HD">HD</span>
            <button
              class="like-btn"
              :class="{ liked: isLiked }"
              @click="$emit('like')"
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
                <span class="artist-link" @click="goToArtist(artist)">{{ artist }}</span>
                <span v-if="index < parsedArtists.length - 1" class="artist-sep">, </span>
              </template>
            </template>
            <span v-else>{{ getDisplayArtist(track) }}</span>
          </p>
          <TrackTags
            v-if="track?.id"
            :trackId="track.id"
            :tags="track.tags || []"
            :interactive="true"
            :max="6"
            class="player-tags"
            @tagClick="handleTagClick"
          />
        </div>

        <!-- Progress bar -->
        <div class="body-progress">
          <div class="slider-wrapper">
            <div class="buffered-bar" :style="{ width: (buffered / (duration || 1)) * 100 + '%' }"/>
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

        <!-- Volume -->
        <div class="body-volume">
          <button class="volume-btn" @click="$emit('toggleMute')">
            <svg v-if="isMuted || volume === 0" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
            </svg>
            <svg v-else-if="volume < 0.5" width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>
            </svg>
            <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
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
          <button
            class="lyrics-toggle-btn"
            :class="{ active: showLyrics }"
            @click="showLyrics = !showLyrics; if (showLyrics) showQueue = false"
            title="Текст"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              <line x1="8" y1="8" x2="16" y2="8"/>
              <line x1="8" y1="12" x2="13" y2="12"/>
            </svg>
          </button>
          <button
            class="queue-toggle-btn"
            :class="{ active: showQueue }"
            @click="showQueue = !showQueue; if (showQueue) showLyrics = false"
            title="Очередь"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
              <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
            </svg>
          </button>
        </div>

        <!-- Lyrics overlay -->
        <Transition name="slide-up-overlay">
          <div v-if="showLyrics" class="overlay-panel lyrics-panel">
            <LyricsViewer
              :track="track"
              :currentTime="progress"
              :isPlaying="isPlaying"
              @seek="$emit('seek', $event)"
              @close="showLyrics = false"
            />
          </div>
        </Transition>

        <!-- Queue panel -->
        <Transition name="slide-up-overlay">
          <div v-if="showQueue" class="overlay-panel queue-panel">
            <div class="queue-header">
              <span>Очередь</span>
              <span class="queue-hint">← свайп для удаления</span>
              <button @click="showQueue = false" class="close-queue">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
                </svg>
              </button>
            </div>
            <div class="queue-list">
              <div
                v-for="(t, idx) in upcomingQueue"
                :key="`q-${t.id}-${idx}`"
                class="queue-item"
                :class="{
                  swiping: swipingQueueIndex === idx,
                  'swipe-delete': swipeDeleteProgress > 0.5 && swipingQueueIndex === idx,
                }"
                :style="getQueueItemStyle(idx)"
                @touchstart.passive="onQueueTouchStart($event, idx)"
                @touchmove="onQueueTouchMove($event, idx)"
                @touchend="onQueueTouchEnd($event, idx)"
                @click="$emit('playFromQueue', idx)"
                @contextmenu.prevent="openMenu('track', t, 'queue', $event)"
              >
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  getTrackCoverStyle, getTrackInitials, getAllTrackArtists,
  getDisplayTitle, getDisplayArtist, getCoverUrl, CoverSize
} from '@/utils'
import TrackTags from '@/components/TrackTags.vue'
import LyricsViewer from '@/components/LyricsViewer.vue'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { useNetworkMonitor } from '@/composables/useNetworkMonitor'

const props = defineProps({
  track: Object,
  isPlaying: Boolean,
  loading: { type: Boolean, default: false },
  progress: Number,
  duration: Number,
  buffered: { type: Number, default: 0 },
  volume: { type: Number, default: 1 },
  isMuted: { type: Boolean, default: false },
  shuffle: Boolean,
  repeat: String,
  isLiked: { type: Boolean, default: false },
  queue: { type: Array, default: () => [] },
  queueIndex: { type: Number, default: -1 },
  shuffleOrder: { type: Array, default: () => [] },
  shuffleIndex: { type: Number, default: -1 },
  lazyShuffleMode: { type: Boolean, default: false },
  lazyShuffleTotal: { type: Number, default: 0 },
  lazyShuffleIndex: { type: Number, default: -1 },
})

const emit = defineEmits([
  'toggle', 'next', 'prev', 'seek', 'setVolume', 'toggleMute',
  'toggleShuffle', 'toggleRepeat', 'like',
  'removeFromQueue', 'moveInQueue', 'playFromQueue',
  'update:expanded', 'update:expandProgress',
])

const router = useRouter()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()
const networkMonitor = useNetworkMonitor()
const telegram = inject('telegram')

// ─── Expand state ───
const expandProgress = ref(0)  // 0 = collapsed, 1 = expanded
const isExpanded = ref(false)
const isAnimating = ref(false)
const isDragging = ref(false)

// ─── Refs ───
const headerRef = ref(null)
const bodyRef = ref(null)

// ─── Panels ───
const showQueue = ref(false)
const showLyrics = ref(false)

// ─── Sizing constants ───
const HEADER_COLLAPSED_H = 86  // px — mini player height
const HEADER_EXPANDED_H = 64   // px — compact bar height
const NAV_H = 64               // px — nav bar height

// ─── Sheet classes & style ───
const sheetClasses = computed(() => ({
  'sheet--expanded': isExpanded.value,
  'sheet--dragging': isDragging.value,
  'sheet--animating': isAnimating.value,
}))

const sheetStyle = computed(() => ({
  '--expand': expandProgress.value,
  '--header-h-collapsed': HEADER_COLLAPSED_H + 'px',
  '--header-h-expanded': HEADER_EXPANDED_H + 'px',
}))

// ─── Expand/Collapse ───
const expand = () => {
  isAnimating.value = true
  expandProgress.value = 1
  isExpanded.value = true
  emit('update:expanded', true)
  emit('update:expandProgress', 1)
  setTimeout(() => { isAnimating.value = false }, 400)
}

const collapse = () => {
  isAnimating.value = true
  expandProgress.value = 0
  isExpanded.value = false
  showQueue.value = false
  showLyrics.value = false
  emit('update:expanded', false)
  emit('update:expandProgress', 0)
  setTimeout(() => { isAnimating.value = false }, 400)
}

const handleHeaderTap = () => {
  if (isDragging.value) return
  if (!isExpanded.value) {
    expand()
  }
}

// ─── Touch gesture for expand/collapse ───
let touchStartY = 0
let touchStartTime = 0
let touchStartProgress = 0
let lastVelocity = 0
let velocityPoints = []
let touchMoved = false

const onTouchStart = (e) => {
  if (isAnimating.value) return
  const touch = e.touches[0]
  touchStartY = touch.clientY
  touchStartTime = Date.now()
  touchStartProgress = expandProgress.value
  touchMoved = false
  velocityPoints = [{ y: touch.clientY, t: Date.now() }]
}

const onTouchMove = (e) => {
  if (isAnimating.value) return
  const touch = e.touches[0]
  const deltaY = touchStartY - touch.clientY  // positive = swipe up
  const screenH = window.innerHeight

  if (Math.abs(deltaY) > 8) {
    touchMoved = true
    isDragging.value = true
  }

  if (!isDragging.value) return

  e.preventDefault()

  // Track velocity
  velocityPoints.push({ y: touch.clientY, t: Date.now() })
  if (velocityPoints.length > 6) velocityPoints.shift()

  // Calculate progress based on drag distance
  const travel = screenH - HEADER_COLLAPSED_H - NAV_H
  const rawProgress = touchStartProgress + (deltaY / travel)
  expandProgress.value = Math.max(0, Math.min(1, rawProgress))
  emit('update:expandProgress', expandProgress.value)
}

const onTouchEnd = () => {
  if (!isDragging.value && !touchMoved) return
  isDragging.value = false

  // Calculate velocity from last few points
  if (velocityPoints.length >= 2) {
    const last = velocityPoints[velocityPoints.length - 1]
    const first = velocityPoints[Math.max(0, velocityPoints.length - 4)]
    const dt = last.t - first.t
    if (dt > 0) {
      lastVelocity = (first.y - last.y) / dt  // px/ms, positive = upward
    }
  }

  // Snap decision
  const threshold = 0.3
  const velocityThreshold = 0.5  // px/ms

  if (Math.abs(lastVelocity) > velocityThreshold) {
    // Use velocity direction
    if (lastVelocity > 0) {
      expand()
    } else {
      collapse()
    }
  } else {
    // Use position threshold
    if (expandProgress.value > threshold) {
      expand()
    } else {
      collapse()
    }
  }
}

// ─── Computed display ───
const displayText = computed(() => {
  const artist = getDisplayArtist(props.track)
  const title = getDisplayTitle(props.track)
  return `${artist} — ${title}`
})

const shouldMarquee = computed(() => displayText.value.length > 30)

const coverStyle = computed(() => getTrackCoverStyle(props.track))
const coverInitials = computed(() => getTrackInitials(props.track))

const coverThumbStyle = computed(() => {
  if (props.track?.cover_url) return {}
  return getTrackCoverStyle(props.track)
})

const parsedArtists = computed(() => {
  const t = props.track
  if (!t) return []
  return getAllTrackArtists(t.artist, t.title, t.file_name)
})

// ─── Progress helpers ───
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

const getDotClass = (index, total = 20) => {
  const dotPercent = (index / total) * 100
  const prevDotPercent = ((index - 1) / total) * 100
  if (dotPercent <= progressPercent.value) return 'active'
  if (prevDotPercent < progressPercent.value && dotPercent > progressPercent.value) return 'next'
  if (dotPercent <= bufferedPercent.value) return 'buffered'
  return ''
}

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// ─── Cover swipe for prev/next ───
const isCoverSwiping = ref(false)
const coverSwipeDir = ref(null)
let coverTouchStart = { x: 0, y: 0 }
let coverTouchCurrent = { x: 0, y: 0 }
let coverLongPressTimer = null
let coverTouchMoved = false
const COVER_SWIPE_THRESHOLD = 80

const onCoverTouchStart = (e) => {
  const touch = e.touches[0]
  coverTouchStart = { x: touch.clientX, y: touch.clientY }
  coverTouchCurrent = { x: touch.clientX, y: touch.clientY }
  isCoverSwiping.value = false
  coverSwipeDir.value = null
  coverTouchMoved = false

  clearTimeout(coverLongPressTimer)
  coverLongPressTimer = setTimeout(() => {
    if (!coverTouchMoved) {
      telegram?.HapticFeedback?.impactOccurred?.('heavy')
      openTrackContextMenu()
    }
  }, 500)
}

const onCoverTouchMove = (e) => {
  const touch = e.touches[0]
  coverTouchCurrent = { x: touch.clientX, y: touch.clientY }
  const deltaX = coverTouchCurrent.x - coverTouchStart.x
  const deltaY = coverTouchCurrent.y - coverTouchStart.y

  if (Math.abs(deltaX) > 12 || Math.abs(deltaY) > 12) {
    coverTouchMoved = true
    clearTimeout(coverLongPressTimer)
  }

  if (Math.abs(deltaX) > 20 && Math.abs(deltaX) > Math.abs(deltaY)) {
    isCoverSwiping.value = true
    coverSwipeDir.value = deltaX > 0 ? 'right' : 'left'
  }
}

const onCoverTouchEnd = () => {
  clearTimeout(coverLongPressTimer)
  const deltaX = coverTouchCurrent.x - coverTouchStart.x
  const deltaY = coverTouchCurrent.y - coverTouchStart.y

  if (deltaX < -COVER_SWIPE_THRESHOLD && Math.abs(deltaX) > Math.abs(deltaY)) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('next')
  } else if (deltaX > COVER_SWIPE_THRESHOLD && Math.abs(deltaX) > Math.abs(deltaY)) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('prev')
  }

  isCoverSwiping.value = false
  coverSwipeDir.value = null
}

// ─── Queue ───
const upcomingQueue = computed(() => {
  if (!props.queue.length || props.queueIndex < 0) return []
  if (props.shuffle && props.shuffleOrder.length > 0 && props.shuffleIndex >= 0) {
    const upcoming = []
    for (let i = 1; i <= 5; i++) {
      const nextShuffleIdx = props.shuffleIndex + i
      if (nextShuffleIdx >= props.shuffleOrder.length) break
      const queueIdx = props.shuffleOrder[nextShuffleIdx]
      if (props.queue[queueIdx]) upcoming.push(props.queue[queueIdx])
    }
    return upcoming
  }
  return props.queue.slice(props.queueIndex + 1, props.queueIndex + 6)
})

const swipingQueueIndex = ref(-1)
const swipeStartX = ref(0)
const swipeCurrentX = ref(0)
const swipeDeleteProgress = ref(0)
const QUEUE_SWIPE_DELETE_THRESHOLD = 100

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
  if (deltaX > 0) {
    e.preventDefault()
    swipeDeleteProgress.value = Math.min(1, deltaX / QUEUE_SWIPE_DELETE_THRESHOLD)
  }
}

const onQueueTouchEnd = (e, idx) => {
  if (swipingQueueIndex.value !== idx) return
  const deltaX = swipeStartX.value - swipeCurrentX.value
  if (deltaX > QUEUE_SWIPE_DELETE_THRESHOLD) {
    telegram?.HapticFeedback?.impactOccurred?.('medium')
    emit('removeFromQueue', idx)
  }
  swipingQueueIndex.value = -1
  swipeStartX.value = 0
  swipeCurrentX.value = 0
  swipeDeleteProgress.value = 0
}

const getQueueItemStyle = (idx) => {
  if (swipingQueueIndex.value === idx && swipeDeleteProgress.value > 0) {
    const translateX = -(swipeDeleteProgress.value * QUEUE_SWIPE_DELETE_THRESHOLD)
    return { transform: `translateX(${translateX}px)`, transition: 'none' }
  }
  return {}
}

// ─── Navigation ───
const goToArtist = (artistName) => {
  if (artistName) {
    router.push(`/artist/${encodeURIComponent(artistName)}`)
    collapse()
  }
}

const handleTagClick = (tag) => {
  console.log('[MobilePlayerSheet] Tag clicked:', tag)
}

const openTrackContextMenu = () => {
  telegram?.HapticFeedback?.impactOccurred?.('light')
  openMenu('track', props.track, 'player')
}

// ─── Expose for parent ───
defineExpose({ expand, collapse, isExpanded, expandProgress })
</script>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   🎵 MOBILE PLAYER SHEET — Swipe-Up Fullscreen Player
   All states driven by --expand custom property (0 → 1)
   ═══════════════════════════════════════════════════════════ */

/* ─── Sheet Root ─── */
.player-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  /* When collapsed: only the header peeks above the navbar */
  /* When expanded: covers the full screen above navbar */
  z-index: 90;
  pointer-events: none;
}

.player-sheet > * {
  pointer-events: auto;
}

/* ─── Backdrop ─── */
.sheet-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  opacity: calc(var(--expand) * 1);
  pointer-events: none;
  transition: opacity 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  z-index: -1;
}

.sheet--expanded .sheet-backdrop,
.sheet--dragging .sheet-backdrop {
  pointer-events: auto;
}

.sheet--dragging .sheet-backdrop {
  transition: none;
}

/* ─── Sheet Container ─── */
.sheet-container {
  position: fixed;
  left: 0;
  right: 0;
  /* Bottom: sits above the nav bar (64px + safe area) */
  bottom: calc(64px + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - env(safe-area-inset-bottom, 0px));
  max-height: calc(100dvh - env(safe-area-inset-bottom, 0px));
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
}

.sheet--dragging .sheet-container {
  transition: none;
}

/* ─── Sheet Header ─── */
.sheet-header {
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  /* Height interpolates between collapsed and expanded */
  height: calc(
    var(--header-h-collapsed) +
    (var(--header-h-expanded) - var(--header-h-collapsed)) * var(--expand)
  );
  overflow: hidden;
  z-index: 2;
}

/* ─── Drag Handle ─── */
.sheet-drag-handle {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.drag-pill {
  width: 36px;
  height: 4px;
  border-radius: var(--r-full);
  background: rgba(255, 255, 255, 0.25);
  transition: background 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.sheet-header:active .drag-pill {
  background: rgba(255, 255, 255, 0.5);
}

/* ─── Collapsed Header (LCD mini-player) ─── */
.header-collapsed {
  position: absolute;
  inset: 0;
  padding: 16px 10px 6px;
  opacity: calc(1 - var(--expand) * 2.5);  /* fades out quickly */
  transform: scale(calc(1 - var(--expand) * 0.05));
  pointer-events: all;
  transition: opacity 0.25s ease, transform 0.3s ease;
}

.sheet--dragging .header-collapsed {
  transition: none;
}

.sheet--expanded .header-collapsed {
  pointer-events: none;
}

/* ─── Expanded Header (compact bar) ─── */
.header-expanded {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  opacity: calc(var(--expand) * 2.5 - 1.0); /* fades in late */
  pointer-events: none;
  transition: opacity 0.25s ease;
  background: rgba(14, 18, 24, 0.95);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sheet--dragging .header-expanded {
  transition: none;
}

.sheet--expanded .header-expanded {
  pointer-events: auto;
}

.collapse-btn {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-radius: var(--r-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--c-text-1);
  transition: all 0.18s ease;
  box-shadow:
    3px 4px 8px rgba(0, 0, 0, 0.4),
    -1px -1px 3px rgba(255, 255, 255, 0.05),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.collapse-btn:active {
  transform: scale(0.9);
  background: rgba(0, 0, 0, 0.3);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.6);
}

.expanded-cover {
  width: 44px;
  height: 44px;
  border-radius: var(--r-md);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cover-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-thumb-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
}

.expanded-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.expanded-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expanded-artist {
  font-size: 12px;
  color: var(--c-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expanded-time {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

/* ─── LCD Screen (Nokia XpressMusic) ─── */
.lcd-screen {
  flex: 1;
  background: linear-gradient(180deg, rgba(8, 16, 24, 0.85) 0%, rgba(4, 10, 16, 0.95) 100%);
  border-radius: var(--r-md);
  padding: 10px 12px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  border: 1px solid rgba(77, 195, 255, 0.15);
  box-shadow:
    inset 0 2px 10px rgba(0, 0, 0, 0.8),
    0 1px 0 rgba(255, 255, 255, 0.05);
  min-width: 0;
  position: relative;
  overflow: visible;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lcd-screen::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0, 0, 0, 0.03) 2px, rgba(0, 0, 0, 0.03) 4px
  );
  pointer-events: none;
  border-radius: inherit;
}

/* LCD rows */
.lcd-row { display: flex; align-items: center; gap: 10px; min-width: 0; position: relative; z-index: 1; }
.row-title { justify-content: space-between; }

.lcd-title-container {
  flex: 1; min-width: 0; overflow: hidden;
  mask-image: linear-gradient(90deg, black 90%, transparent 100%);
  -webkit-mask-image: linear-gradient(90deg, black 90%, transparent 100%);
}

.lcd-title-track { display: inline-flex; white-space: nowrap; }
.lcd-title-track.marquee { animation: marquee-scroll 12s linear infinite; }
.lcd-title {
  color: var(--lcd-text);
  font-size: 14px; font-weight: 600; letter-spacing: 0.3px;
  text-shadow: 0 0 8px var(--lcd-glow);
  white-space: nowrap; flex-shrink: 0;
}
.lcd-title-clone { margin-left: 60px; }

@keyframes marquee-scroll {
  0%, 5% { transform: translateX(0); }
  95%, 100% { transform: translateX(calc(-50% - 30px)); }
}

/* LCD Indicators */
.lcd-indicators { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.lcd-indicator {
  display: flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 4px;
  color: var(--lcd-dot-off); opacity: 0.4;
  transition: all 0.2s ease; cursor: pointer;
}
.lcd-indicator:active { transform: scale(0.9); }
.lcd-indicator.active { opacity: 1; color: var(--lcd-text); text-shadow: 0 0 6px var(--lcd-glow); }
.lcd-indicator.hd-indicator { cursor: default; }
.lcd-indicator.hd-indicator.active { color: #ffd700; text-shadow: 0 0 8px rgba(255, 215, 0, 0.8); }
.lcd-indicator.like-indicator.active { opacity: 1; color: #ff4b7b; text-shadow: 0 0 8px rgba(255, 75, 123, 0.7); }
.lcd-indicator.like-indicator.active svg { filter: drop-shadow(0 0 4px rgba(255, 75, 123, 0.8)); }
.lcd-indicator.net-indicator.active { color: #ff6b6b; text-shadow: 0 0 8px rgba(255, 107, 107, 0.8); cursor: default; }
.lcd-indicator.net-indicator.pulse { animation: net-pulse 1.5s ease-in-out infinite; }
@keyframes net-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* LCD Controls Row */
.row-controls { gap: 8px; }

.lcd-buttons {
  display: flex; flex-shrink: 0; border-radius: 6px; overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.lcd-btn {
  width: 32px; height: 26px; border: none; background: transparent;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--lcd-text); transition: all 0.15s ease; position: relative;
}
.lcd-btn:first-child::after {
  content: ''; position: absolute; right: 0; top: 4px; bottom: 4px;
  width: 1px; background: rgba(255, 255, 255, 0.1);
}
.lcd-btn:active { background: rgba(0, 0, 0, 0.3); }
.lcd-btn:active svg { color: var(--c-accent); filter: drop-shadow(0 0 4px var(--c-accent-glow)); }

/* LCD Progress Dots */
.lcd-progress { flex: 1; display: flex; align-items: center; gap: 2px; min-width: 0; }
.lcd-dot {
  flex: 1; height: 4px; min-width: 2px;
  background: var(--lcd-dot-off); border-radius: 2px;
  transition: background 0.15s ease, box-shadow 0.15s ease;
}
.lcd-dot.active { background: var(--c-accent); box-shadow: 0 0 4px var(--c-accent-glow); }
.lcd-dot.buffered { background: rgba(0, 188, 212, 0.3); }
.lcd-dot.next { background: var(--c-accent); opacity: 0.5; animation: dot-blink 0.6s ease-in-out infinite; }
@keyframes dot-blink {
  0%, 100% { opacity: 0.3; box-shadow: none; }
  50% { opacity: 1; box-shadow: 0 0 6px var(--c-accent-glow); }
}

/* LCD Time */
.lcd-time {
  font-size: 11px; font-weight: 600; color: var(--lcd-text);
  text-shadow: 0 0 6px var(--lcd-glow);
  font-variant-numeric: tabular-nums; letter-spacing: 0.5px;
  flex-shrink: 0; min-width: 65px; text-align: right;
}

/* ─── Sheet Body (fullscreen content) ─── */
.sheet-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  /* Hidden when collapsed */
  opacity: var(--expand);
  transform: translateY(calc((1 - var(--expand)) * 40px));
  pointer-events: none;
  transition: opacity 0.3s ease, transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  background: radial-gradient(circle at 50% 25%, rgba(35, 45, 60, 0.5) 0%, rgba(10, 12, 16, 0.98) 80%);
  min-height: 0;
}

.sheet--expanded .sheet-body {
  pointer-events: auto;
}

.sheet--dragging .sheet-body {
  transition: none;
}

/* ─── Background behind header when collapsed ─── */
.sheet-header {
  background: rgba(14, 18, 24, 0.85);
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.45);
}

/* ─── Cover Art ─── */
.body-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 8px 0;
  flex-shrink: 0;
}

.cover-image {
  width: 100%;
  max-width: min(280px, 40vh);
  aspect-ratio: 1;
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 16px 36px rgba(0, 0, 0, 0.65),
    0 0 50px rgba(29, 185, 84, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.12);
  position: relative;
}

.body-cover.swiping .cover-image {
  transform: scale(0.93);
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  font-size: 72px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 4px 14px rgba(0, 0, 0, 0.6);
}

/* Loading overlay */
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 5;
  border-radius: 22px;
}
.loading-spinner { color: var(--c-accent); animation: spin 1s linear infinite; }

/* Swipe arrows */
.swipe-arrows {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none;
}
.arrow { position: absolute; color: var(--c-accent); opacity: 0.9; animation: pulse 0.5s ease infinite; filter: drop-shadow(0 0 10px var(--c-accent-glow)); }
.arrow.left { left: 8%; }
.arrow.right { right: 8%; }
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.15); opacity: 1; }
}

/* ─── Track Info ─── */
.body-info {
  text-align: center;
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
  color: var(--c-text-1);
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.like-btn {
  width: 42px; height: 42px; min-width: 42px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border-radius: var(--r-full);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--c-text-3);
  transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow:
    3px 4px 8px rgba(0, 0, 0, 0.4),
    -1px -1px 3px rgba(255, 255, 255, 0.05),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
}
.like-btn:active {
  transform: scale(0.92);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark), inset -1px -1px 2px var(--sh-inset-light);
}
.like-btn.liked {
  color: #ff4b7b;
  border-color: rgba(255, 75, 123, 0.4);
  background: linear-gradient(145deg, rgba(255, 75, 123, 0.15) 0%, rgba(0, 0, 0, 0.25) 100%);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark), 0 0 14px rgba(255, 75, 123, 0.5);
}
.like-btn.liked svg { filter: drop-shadow(0 0 6px rgba(255, 75, 123, 0.7)); }

/* HD Badge */
.hd-badge {
  padding: 2px 8px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #1a1a2e; border-radius: 4px; margin-left: 8px; flex-shrink: 0;
  animation: hd-badge-pulse 2s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(255, 215, 0, 0.6);
}
@keyframes hd-badge-pulse {
  0%, 100% { box-shadow: 0 0 8px rgba(255, 215, 0, 0.5); }
  50% { box-shadow: 0 0 18px rgba(255, 215, 0, 0.85); }
}

.track-artist { font-size: 15px; color: var(--c-text-2); }
.track-artist .artist-link { cursor: pointer; transition: color 0.2s ease; }
.track-artist .artist-link:hover { color: var(--c-accent); text-decoration: underline; }
.track-artist .artist-sep { color: var(--c-text-2); opacity: 0.6; }
.player-tags { justify-content: center; margin-top: 8px; }

/* ─── Progress Bar ─── */
.body-progress { flex-shrink: 0; }

.slider-wrapper {
  position: relative; width: 100%; height: 6px;
  border-radius: var(--r-full);
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: inset 1px 2px 4px rgba(0, 0, 0, 0.7), inset -1px -1px 2px rgba(255, 255, 255, 0.04);
}

.buffered-bar {
  position: absolute; left: 0; top: 0; height: 100%;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--r-full);
  z-index: 1; pointer-events: none;
  transition: width 0.2s linear;
}

.progress-slider {
  position: absolute; left: 0; top: -6px; width: 100%; height: 18px;
  -webkit-appearance: none; appearance: none;
  background: transparent; outline: none; cursor: pointer;
  z-index: 2; margin: 0;
}
.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px; height: 18px; border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: linear-gradient(145deg, #ffffff 0%, #d4d4d4 100%);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.8), 0 0 10px var(--c-accent-glow);
}
.progress-slider:active::-webkit-slider-thumb {
  transform: scale(1.25);
  background: linear-gradient(145deg, #22e066 0%, #159b43 100%);
}

.progress-times {
  display: flex; justify-content: space-between; margin-top: 8px;
  font-size: 12px; font-weight: 600; color: var(--c-text-3);
  font-variant-numeric: tabular-nums;
}

/* ─── Volume Row ─── */
.body-volume {
  display: flex; align-items: center; gap: 10px;
  flex-shrink: 0; padding: 0 4px;
}

.volume-btn {
  width: 36px; height: 36px; border: none; background: none;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  color: var(--c-text-3); transition: color 0.15s ease; flex-shrink: 0;
}
.volume-btn:active { color: var(--c-accent); }

.volume-slider {
  flex: 1; height: 5px;
  -webkit-appearance: none; appearance: none;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--r-full);
  outline: none; cursor: pointer;
  box-shadow: inset 1px 1px 3px rgba(0, 0, 0, 0.7), inset -1px -1px 2px rgba(255, 255, 255, 0.03);
}
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px; height: 16px; border-radius: var(--r-full);
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: var(--c-text-1); cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.8);
  transition: transform 0.1s ease;
}
.volume-slider:active::-webkit-slider-thumb { transform: scale(1.2); }

.lyrics-toggle-btn, .queue-toggle-btn {
  width: 40px; height: 40px; border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  color: var(--c-text-2);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; flex-shrink: 0;
  box-shadow:
    3px 4px 8px rgba(0, 0, 0, 0.4),
    -1px -1px 3px rgba(255, 255, 255, 0.05),
    inset 0 1px 1px rgba(255, 255, 255, 0.18);
  transition: all 0.18s ease;
}
.lyrics-toggle-btn:active, .queue-toggle-btn:active {
  transform: scale(0.92);
  background: rgba(0, 0, 0, 0.3);
  box-shadow: inset 2px 2px 5px rgba(0, 0, 0, 0.6);
}
.lyrics-toggle-btn.active, .queue-toggle-btn.active {
  color: var(--c-accent);
  border-color: rgba(29, 185, 84, 0.4);
  background: linear-gradient(145deg, rgba(29, 185, 84, 0.15) 0%, rgba(0, 0, 0, 0.25) 100%);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.6), 0 0 14px var(--c-accent-glow);
}

/* ─── Overlay Panels (Lyrics / Queue) ─── */
.overlay-panel {
  position: absolute;
  left: 0; right: 0; bottom: 0;
  top: 0;
  z-index: 50;
}

.lyrics-panel {
  background: rgba(12, 14, 18, 0.96);
  backdrop-filter: blur(36px);
  -webkit-backdrop-filter: blur(36px);
  display: flex; flex-direction: column;
}

.queue-panel {
  background: rgba(18, 22, 28, 0.95);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
  box-shadow: 0 -12px 36px rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-bottom: none;
  top: auto;
  max-height: 60%;
}

.queue-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; font-weight: 700; font-size: 16px; color: var(--c-text-1);
}
.queue-hint { font-size: 11px; color: var(--c-text-3); font-weight: 400; }
.close-queue {
  width: 36px; height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--r-full);
  display: flex; align-items: center; justify-content: center;
  color: var(--c-text-3); cursor: pointer;
  box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.4), -1px -1px 3px rgba(255, 255, 255, 0.04);
  transition: all 0.15s ease;
}
.close-queue:active {
  transform: scale(0.92);
  box-shadow: inset 2px 2px 4px var(--sh-inset-dark);
}

.queue-list { overflow: hidden; }
.queue-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 10px; border-radius: var(--r-md);
  margin-bottom: 8px; cursor: pointer; position: relative;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: transform 0.2s ease, background 0.2s ease;
  user-select: none; touch-action: pan-y;
  box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.3), -1px -1px 3px rgba(255, 255, 255, 0.02);
}
.queue-item:active { background: rgba(255, 255, 255, 0.08); transform: scale(0.98); }
.queue-item.swiping { transition: none; }
.queue-item.swipe-delete {
  background: rgba(229, 57, 53, 0.2);
  box-shadow: 3px 3px 6px var(--sh-dark), -2px -2px 4px var(--sh-light), 0 0 12px rgba(229, 57, 53, 0.3);
}

.queue-num { width: 22px; text-align: center; font-size: 13px; font-weight: 600; color: var(--c-accent); flex-shrink: 0; }
.queue-info { flex: 1; min-width: 0; overflow: hidden; }
.queue-title { display: block; font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--c-text-1); }
.queue-artist { display: block; font-size: 12px; color: var(--c-text-3); }
.delete-indicator {
  position: absolute; right: -40px; top: 50%; transform: translateY(-50%);
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  color: var(--c-accent); opacity: 0; transition: opacity 0.2s;
}
.queue-item.swiping .delete-indicator { opacity: 1; right: 8px; }
.queue-empty { text-align: center; color: var(--c-text-3); padding: 24px; font-size: 14px; }

.queue-lazy-shuffle {
  display: flex; align-items: center; gap: 12px; padding: 16px;
  background: rgba(26, 32, 44, 0.85); border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px; margin: 8px 0;
}
.lazy-shuffle-icon { font-size: 24px; }
.lazy-shuffle-info { display: flex; flex-direction: column; gap: 2px; }
.lazy-shuffle-title { font-weight: 600; color: var(--c-text-1); font-size: 14px; }
.lazy-shuffle-meta { color: var(--c-text-3); font-size: 12px; }

/* ─── Overlay Transitions ─── */
.slide-up-overlay-enter-active,
.slide-up-overlay-leave-active {
  transition: transform 0.3s cubic-bezier(0.2, 0.9, 0.2, 1), opacity 0.25s ease;
}
.slide-up-overlay-enter-from,
.slide-up-overlay-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* ─── Utilities ─── */
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ─── Desktop: hide ─── */
@media (min-width: 1024px) {
  .player-sheet { display: none; }
}
</style>
