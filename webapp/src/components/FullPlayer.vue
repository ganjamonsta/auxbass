<template>
  <div 
    class="full-player"
    ref="playerRef"
  >
    <!-- Tap indicator to minimize -->
    <div class="swipe-indicator" @click="$emit('close')"></div>

    <!-- Header -->
    <div class="player-header">
      <button class="close-btn" @click="$emit('close')" title="Свернуть">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
        </svg>
      </button>
      <span class="player-title">Сейчас играет</span>
      <div class="header-actions">
        <button class="share-header-btn" @click="handleShareTrack" title="Поделиться треком">
          <Share2 :size="18" />
        </button>
        <button class="menu-btn" @click="openTrackContextMenu($event)" title="Меню трека" aria-label="Меню трека">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="5" r="2"/>
            <circle cx="12" cy="12" r="2"/>
            <circle cx="12" cy="19" r="2"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Cover art with generated gradient - swipe area for track navigation & long-press for menu -->
    <div 
      class="player-cover" 
      :class="{ swiping: isSwiping }"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
      @touchcancel="onTouchEnd"
      @contextmenu.prevent="openTrackContextMenu"
    >
      <div class="cover-image" :style="coverStyle">
        <span v-if="!track?.cover_url" class="cover-text">{{ coverInitials }}</span>
        <img v-else :src="getCoverUrl(track.cover_url, CoverSize.XL)" alt="Cover" class="cover-img" />
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
    <div class="player-info" @contextmenu.prevent="openTrackContextMenu">
      <div class="track-info-row">
        <h2 class="track-title">{{ getDisplayTitle(track) }}</h2>
        <!-- HD indicator badge -->
        <span v-if="playerStore.hdTrackInfo" class="hd-badge" title="HD версия доступна для скачивания">
          HD
        </span>
        <span v-else-if="track?.is_chunk" class="chunk-badge" title="30-секундный ознакомительный фрагмент">
          ✂️ 30s превью
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
        <span v-else-if="getDisplayArtist(track)" class="artist-link" @click="goToArtist(getDisplayArtist(track))">
          {{ getDisplayArtist(track) }}
        </span>
      </p>
      <!-- Clickable Album link if track belongs to an album -->
      <p v-if="trackAlbum" class="track-album-subtitle" @click="goToAlbum">
        <Disc3 :size="13" class="album-icon" />
        <span class="album-link">{{ trackAlbum.name }}</span>
      </p>
      <!-- Interactive tags with voting -->
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
        class="lyrics-toggle-btn" 
        :class="{ active: showLyrics }"
        @click="showLyrics = !showLyrics; if (showLyrics) showQueue = false"
        title="Текст песни"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          <line x1="8" y1="8" x2="16" y2="8"></line>
          <line x1="8" y1="12" x2="13" y2="12"></line>
        </svg>
      </button>
      <button 
        class="queue-toggle-btn" 
        :class="{ active: showQueue }"
        @click="showQueue = !showQueue; if (showQueue) showLyrics = false"
        title="Очередь"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <path d="M4 10h12v2H4zm0-4h12v2H4zm0 8h8v2H4zm10 0v6l5-3z"/>
        </svg>
      </button>
    </div>

    <!-- Full Lyrics overlay -->
    <Transition name="slide-up-lyrics">
      <div v-if="showLyrics" class="player-lyrics-container">
        <LyricsViewer 
          :track="track" 
          :currentTime="progress" 
          :isPlaying="isPlaying" 
          @seek="$emit('seek', $event)" 
          @close="showLyrics = false"
        />
      </div>
    </Transition>

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
            v-longpress="(e) => openMenu('track', t, 'queue', e)"
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
import { Disc3, Share2 } from 'lucide-vue-next'
import { getTrackCoverStyle, getTrackInitials, splitArtists, getDisplayTitle, getDisplayArtist, getAllTrackArtists, getCoverUrl, CoverSize, suppressNextClick, suppressNextContextMenu } from '@/utils'
import TagChips from '@/components/TagChips.vue'
import TrackTags from '@/components/TrackTags.vue'
import LyricsViewer from '@/components/LyricsViewer.vue'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { useAuthStore } from '@/stores/auth'
import { useShare } from '@/composables/useShare'
import { albumsApi } from '@/api/client'

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
const uiStore = useUIStore()
const authStore = useAuthStore()
const { openMenu } = useContextMenu()
const { openShare } = useShare()

const handleShareTrack = () => {
  if (!props.track?.id) return
  openShare({
    type: 'track',
    id: props.track.id,
    title: getDisplayTitle(props.track),
    subtitle: getDisplayArtist(props.track) || 'Неизвестен',
    coverUrl: props.track.cover_url || '',
  })
}

const telegram = inject('telegram')

// Parse artists into separate names (from artist + title + file_name)
const parsedArtists = computed(() => {
  const t = props.track
  if (!t) return []
  return getAllTrackArtists(t.artist, t.title, t.file_name)
})

// Navigate to artist page
const goToArtist = (artistName) => {
  if (artistName) {
    router.push(`/artist/${encodeURIComponent(artistName)}`)
    emit('close')
  }
}

// Parse track album info if available
const trackAlbum = computed(() => {
  const t = props.track
  if (!t) return null
  if (t.album && typeof t.album === 'object' && t.album.id) {
    return t.album
  }
  if (t.album_id && (t.album_name || t.album_title)) {
    return {
      id: t.album_id,
      name: t.album_name || t.album_title
    }
  }
  if (t.album_name || t.album?.name || (typeof t.album === 'string' && t.album.trim())) {
    return {
      id: null,
      name: t.album_name || t.album?.name || t.album
    }
  }
  return null
})

// Navigate to album page
const goToAlbum = async () => {
  if (trackAlbum.value?.id) {
    router.push(`/album/${trackAlbum.value.id}`)
    emit('close')
    return
  }

  const t = props.track
  const albumName = trackAlbum.value?.name || t?.album_name || (typeof t?.album === 'string' ? t.album : null)
  if (t?.id || albumName) {
    emit('close')
    try {
      const res = await albumsApi.resolve({
        track_id: t?.id,
        album_name: albumName,
        artist: t?.artist
      })
      if (res?.data?.album_id) {
        router.push(`/album/${res.data.album_id}`)
      } else {
        uiStore.toast.info('Альбом', 'Альбом не найден')
      }
    } catch (err) {
      console.error('Failed to resolve album:', err)
      uiStore.toast.error('Ошибка', 'Не удалось открыть альбом')
    }
  }
}

// Navigate to tag search
const handleTagClick = (tag) => {
  if (!tag) return
  emit('close')
  const cleanTag = tag.replace(/^#/, '')
  router.push({ path: '/search', query: { tag: cleanTag } })
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
const showLyrics = ref(false)

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

let coverLongPressTimer = null
let coverTouchMoved = false

const onTouchStart = (e) => {
  const touch = e.touches[0]
  touchStart.value = { x: touch.clientX, y: touch.clientY }
  touchCurrent.value = { x: touch.clientX, y: touch.clientY }
  isSwiping.value = false
  swipeDirection.value = null
  coverTouchMoved = false

  clearTimeout(coverLongPressTimer)
  coverLongPressTimer = setTimeout(() => {
    if (!coverTouchMoved) {
      telegram?.HapticFeedback?.impactOccurred?.('heavy')
      suppressNextClick()
      suppressNextContextMenu()
      openTrackContextMenu()
    }
  }, 500)
}

const onTouchMove = (e) => {
  const touch = e.touches[0]
  touchCurrent.value = { x: touch.clientX, y: touch.clientY }
  
  const deltaX = touchCurrent.value.x - touchStart.value.x
  const deltaY = touchCurrent.value.y - touchStart.value.y
  
  if (Math.abs(deltaX) > 12 || Math.abs(deltaY) > 12) {
    coverTouchMoved = true
    clearTimeout(coverLongPressTimer)
  }
  
  // Only handle horizontal swipes for track navigation
  if (Math.abs(deltaX) > 20 && Math.abs(deltaX) > Math.abs(deltaY)) {
    isSwiping.value = true
    swipeDirection.value = deltaX > 0 ? 'right' : 'left'
  }
}

const onTouchEnd = () => {
  clearTimeout(coverLongPressTimer)
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

<style scoped src="./FullPlayer.css"></style>
