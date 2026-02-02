<template>
  <aside class="now-playing-sidebar">
    <!-- Header -->
    <div class="sidebar-header">
      <span class="header-title">Сейчас играет</span>
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
import { computed, defineEmits } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useContextMenu } from '@/composables/useContextMenu'
import { splitArtists, getDisplayTitle, getDisplayArtist, getAllTrackArtists, getCoverUrl, CoverSize } from '@/utils/formatters'
import { Play } from 'lucide-vue-next'

const emit = defineEmits(['goToUser'])

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const { openMenu } = useContextMenu()

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
  return libraryStore.isTrackLiked(track.value.id)
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
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

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
    await libraryStore.toggleLike(track.value.id)
  }
}
</script>

<style scoped>
.now-playing-sidebar {
  width: 320px;
  background: #0a0a0a;
  border-left: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow-x: hidden;
  overflow-y: auto;
  height: 100%;
}

/* Header */
.sidebar-header {
  margin-bottom: 16px;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Cover Container */
.cover-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  overflow: hidden;
  flex-shrink: 0;
  min-height: 240px;
}

.cover-wrapper {
  position: relative;
  width: 240px;
  height: 240px;
  min-width: 240px;
  min-height: 240px;
  overflow: hidden;
}

.cover-art {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  transition: transform 0.3s ease;
}

.cover-wrapper.playing .cover-art {
  transform: scale(0.95);
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-text {
  font-size: 64px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

/* Vinyl disc effect */
.vinyl-disc {
  position: absolute;
  z-index: 1;
  top: 50%;
  left: 50%;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
  transform: translate(-50%, -50%) translateX(0);
  opacity: 0;
  transition: all 0.4s ease;
}

.cover-wrapper.playing .vinyl-disc {
  opacity: 1;
  transform: translate(-50%, -50%) translateX(60px);
}

.vinyl-disc.spinning {
  animation: spin 3s linear infinite;
}

@keyframes spin {
  from { transform: translate(-50%, -50%) translateX(60px) rotate(0deg); }
  to { transform: translate(-50%, -50%) translateX(60px) rotate(360deg); }
}

.vinyl-grooves {
  position: absolute;
  inset: 20px;
  border-radius: 50%;
  background: repeating-radial-gradient(
    circle at center,
    transparent 0px,
    transparent 2px,
    rgba(255, 255, 255, 0.03) 2px,
    rgba(255, 255, 255, 0.03) 4px
  );
}

.vinyl-label {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1DB954 0%, #169c46 100%);
  transform: translate(-50%, -50%);
}

.vinyl-label::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #1a1a1a;
  transform: translate(-50%, -50%);
}

/* Track Info */
.track-info {
  text-align: center;
  margin-bottom: 16px;
}

.track-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
  margin: 0 0 8px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Artists Container - for split artists */
.artists-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  margin: 4px 2px;
}

.artists-icon {
  flex-shrink: 0;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.7);
}

.artists-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.artist-link-inline {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s ease;
}

.artist-link-inline:hover {
  color: #1DB954;
  text-decoration: underline;
}

.artist-separator {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

/* Info Links */
.info-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 20px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  margin: 4px 2px;
}

.info-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.info-link svg {
  flex-shrink: 0;
  opacity: 0.7;
}

.info-link .external-icon {
  opacity: 0.5;
  margin-left: 2px;
}

.artist-link:hover {
  color: #1DB954;
}

.album-link:hover {
  color: #1db954;
}

.forward-link:hover {
  color: #29b6f6;
}

.info-text {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.info-text.muted {
  color: rgba(255, 255, 255, 0.4);
}

/* Divider */
.sidebar-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 12px 0;
}

/* Source Info */
.source-info {
  padding: 8px 0;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 12px 0;
}

.source-info .info-link,
.source-info .info-text {
  width: 100%;
  justify-content: flex-start;
  margin: 4px 0;
}

/* Stats */
.track-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.stat-item svg {
  opacity: 0.6;
}

/* Actions */
.track-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 16px;
}

.action-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.action-btn.active {
  background: rgba(255, 64, 129, 0.15);
  color: #ff4081;
}

.action-btn.active svg {
  fill: #ff4081;
}

/* Queue Section */
.queue-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.queue-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.empty-queue {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
}

.queue-list {
  flex: 1;
  overflow-y: auto;
  margin: 0 -8px;
  padding: 0 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.queue-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.queue-item.current {
  background: rgba(29, 185, 84, 0.1);
}

.queue-item.current .queue-item-title {
  color: #1DB954;
}

.queue-item-number {
  width: 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.queue-item.current .queue-item-number {
  color: #1DB954;
}

.playing-icon {
  fill: #1DB954;
}

.queue-item-cover {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.queue-cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.queue-cover-placeholder {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.3);
}

.queue-item-info {
  flex: 1;
  min-width: 0;
}

.queue-item-title {
  font-size: 13px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-item-artist {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.queue-item-remove {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.queue-item:hover .queue-item-remove {
  opacity: 1;
}

.queue-item-remove:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
}

/* Uploader link */
.uploader-link:hover {
  color: #29b6f6;
}

/* Scrollbar */
.now-playing-sidebar {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.now-playing-sidebar::-webkit-scrollbar {
  width: 8px;
}

.now-playing-sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  margin: 8px 0;
}

.now-playing-sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.now-playing-sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
  border: 2px solid transparent;
  background-clip: padding-box;
}

.now-playing-sidebar::-webkit-scrollbar-thumb:active {
  background: rgba(255, 255, 255, 0.35);
}

/* Queue list scrollbar */
.queue-list {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}

.queue-list::-webkit-scrollbar {
  width: 6px;
}

.queue-list::-webkit-scrollbar-track {
  background: transparent;
}

.queue-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}

.queue-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
