<template>
  <aside class="now-playing-sidebar">
    <!-- Header -->
    <div class="sidebar-header">
      <span class="header-title">Сейчас играет</span>
      <button 
        class="now-playing-close-btn" 
        @click="uiStore.setNowPlayingSidebar(false, true)"
        title="Скрыть панель"
        aria-label="Скрыть панель"
      >
        <PanelRightClose :size="18" />
      </button>
    </div>

    <!-- Large Cover Art -->
    <div class="cover-container">
      <div class="cover-wrapper" :class="{ playing: isPlaying }">
        <div class="cover-art" :style="coverStyle">
          <img 
            v-if="track?.cover_url" 
            :src="getCoverUrl(track.cover_url, CoverSize.XL)" 
            alt="Cover" 
            class="cover-image"
          />
          <span v-else class="cover-text">{{ coverInitials }}</span>
        </div>
        <!-- Vinyl effect -->
        <div class="vinyl-disc" :class="{ spinning: isPlaying }">
          <div class="vinyl-grooves"></div>
          <div class="vinyl-label"></div>
        </div>
      </div>
    </div>

    <!-- Track Info -->
    <div class="track-info">
      <h2 class="track-title">{{ getDisplayTitle(track) }}</h2>
      
      <!-- Artists (clickable, split into separate links) -->
      <div v-if="parsedArtists.length > 0" class="artists-container">
        <svg class="artists-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span class="artists-links">
          <template v-for="(artist, index) in parsedArtists" :key="artist">
            <button 
              class="artist-link-inline"
              @click="goToArtistByName(artist)"
              @contextmenu.prevent="openMenu('artist', { name: artist }, 'sidebar', $event)"
            >{{ artist }}</button>
            <span v-if="index < parsedArtists.length - 1" class="artist-separator">, </span>
          </template>
        </span>
      </div>
      <span v-else class="info-text muted">Неизвестный исполнитель</span>

      <!-- Album (clickable) -->
      <button 
        v-if="track?.album?.id || track?.album_id" 
        class="info-link album-link"
        @click="goToAlbum"
        @contextmenu.prevent="openMenu('album', { id: track.album?.id || track.album_id, name: track.album?.name || track.album_name, album_artist: track.artist }, 'sidebar', $event)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
        </svg>
        <span>{{ track.album?.name || track.album_name || 'Альбом' }}</span>
      </button>
    </div>

    <!-- Divider -->
    <div class="sidebar-divider"></div>

    <!-- Source Info -->
    <div v-if="track?.uploader || track?.forward_source" class="source-info">
      <h3 class="section-title">Источник</h3>

      <!-- Uploader (clickable) -->
      <button 
        v-if="track?.uploader" 
        class="info-link uploader-link"
        @click="goToUploader"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
        </svg>
        <span>{{ uploaderName }}</span>
      </button>

      <!-- Forward source -->
      <a 
        v-if="track?.forward_source?.forward_from_username" 
        class="info-link forward-link"
        :href="forwardSourceUrl"
        target="_blank"
        rel="noopener noreferrer"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
        </svg>
        <span>От: {{ forwardSourceName }}</span>
        <svg class="external-icon" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 19H5V5h7V3H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>
        </svg>
      </a>
      <div 
        v-else-if="track?.forward_source?.forward_from_name" 
        class="info-text forward-text"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z"/>
        </svg>
        <span>От: {{ track.forward_source.forward_from_name }}</span>
      </div>
    </div>

    <!-- Divider -->
    <div v-if="track?.uploader || track?.forward_source" class="sidebar-divider"></div>

    <!-- Stats -->
    <div class="track-stats">
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
        <span>{{ formatPlayCount(track?.play_count || 0) }} прослушиваний</span>
      </div>
      <div v-if="track?.duration" class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
        </svg>
        <span>{{ formatDuration(track.duration) }}</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="track-actions">
      <button 
        class="action-btn" 
        :class="{ active: isLiked }"
        @click="handleToggleLike"
        :title="isLiked ? 'Убрать из любимых' : 'Добавить в любимые'"
      >
        <svg v-if="isLiked" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M16.5 3c-1.74 0-3.41.81-4.5 2.09C10.91 3.81 9.24 3 7.5 3 4.42 3 2 5.42 2 8.5c0 3.78 3.4 6.86 8.55 11.54L12 21.35l1.45-1.32C18.6 15.36 22 12.28 22 8.5 22 5.42 19.58 3 16.5 3zm-4.4 15.55l-.1.1-.1-.1C7.14 14.24 4 11.39 4 8.5 4 6.5 5.5 5 7.5 5c1.54 0 3.04.99 3.57 2.36h1.87C13.46 5.99 14.96 5 16.5 5c2 0 3.5 1.5 3.5 3.5 0 2.89-3.14 5.74-7.9 10.05z"/>
        </svg>
        <span>{{ isLiked ? 'В любимом' : 'Нравится' }}</span>
      </button>

      <button 
        class="action-btn" 
        :class="{ active: showLyrics }"
        @click="showLyrics = !showLyrics"
        :title="showLyrics ? 'Скрыть текст' : 'Показать текст песни'"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          <line x1="8" y1="8" x2="16" y2="8"></line>
          <line x1="8" y1="12" x2="13" y2="12"></line>
        </svg>
        <span>{{ showLyrics ? 'Скрыть текст' : 'Текст песни' }}</span>
      </button>
    </div>

    <!-- Lyrics Section (if enabled) -->
    <div v-if="showLyrics" class="sidebar-lyrics-section">
      <LyricsViewer
        v-if="track"
        :track="track"
        :currentTime="playerStore.progress"
        :isPlaying="isPlaying"
        :embedded="true"
        @seek="playerStore.seek($event)"
      />
    </div>

    <!-- Divider -->
    <div class="sidebar-divider"></div>

    <!-- Queue Section -->
    <div class="queue-section">
      <div class="section-header">
        <h3 class="section-title">Очередь</h3>
        <span class="queue-count">{{ queueLength }} треков</span>
      </div>

      <div v-if="upcomingTracks.length === 0" class="empty-queue">
        <span>Очередь пуста</span>
      </div>

      <div v-else class="queue-list">
        <div 
          v-for="(queueTrack, index) in upcomingTracks" 
          :key="queueTrack.id"
          class="queue-item"
          :class="{ current: index === 0 }"
          @click="playFromQueueHandler(index)"
          @contextmenu.prevent="openMenu('track', queueTrack, 'queue', $event)"
        >
          <div class="queue-item-number">
            <svg v-if="index === 0 && isPlaying" class="playing-icon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <rect x="4" y="4" width="4" height="16" rx="1">
                <animate attributeName="height" values="16;8;16" dur="0.5s" repeatCount="indefinite"/>
                <animate attributeName="y" values="4;8;4" dur="0.5s" repeatCount="indefinite"/>
              </rect>
              <rect x="10" y="4" width="4" height="16" rx="1">
                <animate attributeName="height" values="8;16;8" dur="0.5s" repeatCount="indefinite"/>
                <animate attributeName="y" values="8;4;8" dur="0.5s" repeatCount="indefinite"/>
              </rect>
              <rect x="16" y="4" width="4" height="16" rx="1">
                <animate attributeName="height" values="12;8;12" dur="0.5s" repeatCount="indefinite"/>
                <animate attributeName="y" values="6;8;6" dur="0.5s" repeatCount="indefinite"/>
              </rect>
            </svg>
            <span v-else-if="index === 0"><Play :size="14" fill="currentColor" /></span>
            <span v-else>{{ index }}</span>
          </div>
          <div class="queue-item-cover">
            <img 
              v-if="queueTrack.cover_url" 
              :src="getCoverUrl(queueTrack.cover_url, CoverSize.SMALL)" 
              alt=""
              class="queue-cover-image"
            />
            <span v-else class="queue-cover-placeholder">♪</span>
          </div>
          <div class="queue-item-info">
            <div class="queue-item-title">{{ getDisplayTitle(queueTrack) }}</div>
            <div class="queue-item-artist">{{ getDisplayArtist(queueTrack) }}</div>
          </div>
          <span v-if="queueTrack.duration && index > 0" class="queue-item-duration">{{ formatDuration(queueTrack.duration) }}</span>
          <button 
            v-if="index > 0"
            class="queue-item-remove"
            @click.stop="removeFromQueueHandler(index)"
            title="Убрать из очереди"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, defineEmits } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { splitArtists, getDisplayTitle, getDisplayArtist, getAllTrackArtists, getCoverUrl, CoverSize, formatDuration } from '@/utils/formatters'
import { PanelRightClose } from 'lucide-vue-next'

const uiStore = useUIStore()
import { Play } from 'lucide-vue-next'
import LyricsViewer from '@/components/LyricsViewer.vue'

const emit = defineEmits(['goToUser'])

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const { openMenu } = useContextMenu()

const showLyrics = ref(false)

// Computed from stores
const track = computed(() => playerStore.currentTrack)
const isPlaying = computed(() => playerStore.isPlaying)

// Parse artists into separate names (from artist + title + file_name)
const parsedArtists = computed(() => {
  const t = track.value
  if (!t) return []
  return getAllTrackArtists(t.artist, t.title, t.file_name)
})

// Queue computed
const queue = computed(() => playerStore.queue || [])
const queueIndex = computed(() => playerStore.queueIndex ?? -1)
const queueLength = computed(() => queue.value.length)

// Get upcoming tracks (current + next 10)
const upcomingTracks = computed(() => {
  if (queue.value.length === 0) return []
  const startIdx = Math.max(0, queueIndex.value)
  return queue.value.slice(startIdx, startIdx + 11)
})

const isLiked = computed(() => {
  if (!track.value?.id) return false
  if (libraryStore.isTrackLiked(track.value.id)) return true
  return track.value.is_liked === true
})

// Cover style
const coverStyle = computed(() => {
  if (track.value?.cover_url) return {}
  const str = getDisplayTitle(track.value)
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 60%, 35%) 0%, hsl(${(hue + 40) % 360}, 50%, 25%) 100%)`
  }
})

const coverInitials = computed(() => {
  const title = getDisplayTitle(track.value)
  return title.substring(0, 2).toUpperCase()
})

// Uploader name
const uploaderName = computed(() => {
  const u = track.value?.uploader
  if (!u) return ''
  return u.first_name || u.username || `User ${u.id}`
})

// Forward source
const forwardSourceName = computed(() => {
  const fs = track.value?.forward_source
  if (!fs) return ''
  return fs.forward_from_name || fs.forward_from_username || ''
})

const forwardSourceUrl = computed(() => {
  const fs = track.value?.forward_source
  if (!fs?.forward_from_username) return '#'
  return `https://t.me/${fs.forward_from_username}`
})

// Formatters

const formatPlayCount = (count) => {
  if (!count) return '0'
  if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M'
  if (count >= 1000) return (count / 1000).toFixed(1) + 'K'
  return count.toString()
}

// Navigation
const goToArtist = () => {
  if (track.value?.artist) {
    router.push(`/artist/${encodeURIComponent(track.value.artist)}`)
  }
}

// Navigate to specific artist by name
const goToArtistByName = (artistName) => {
  if (artistName) {
    router.push(`/artist/${encodeURIComponent(artistName)}`)
  }
}

const goToAlbum = () => {
  const albumId = track.value?.album?.id || track.value?.album_id
  if (albumId) {
    router.push(`/album/${albumId}`)
  }
}

// Go to uploader profile
const goToUploader = () => {
  if (track.value?.uploader) {
    emit('goToUser', track.value.uploader)
  }
}

// Queue actions
const playFromQueueHandler = (index) => {
  // index is position in upcomingTracks (0 = current, 1 = next, etc.)
  // playFromQueue expects relative index from current+1
  // so for current track (index 0), we need relativeIndex = -1
  // for next track (index 1), we need relativeIndex = 0
  playerStore.playFromQueue(index - 1)
}

const removeFromQueueHandler = (index) => {
  // index is position in upcomingTracks (0 = current, 1 = next, etc.)
  // removeFromQueue expects relative index from current+1
  // so for index 1 (first upcoming), relativeIndex = 0
  if (index > 0) {
    playerStore.removeFromQueue(index - 1)
  }
}

// Like handler
const handleToggleLike = async () => {
  if (track.value?.id) {
    const current = isLiked.value
    await libraryStore.toggleLike(track.value.id, current)
  }
}
</script>

<style scoped src="./NowPlayingSidebar.css"></style>
