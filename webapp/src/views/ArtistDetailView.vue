<template>
  <!-- Loading skeleton for entire page -->
  <div class="artist-detail-view" v-if="loading && !artist">
    <!-- Artist header skeleton -->
    <div class="artist-header">
      <div class="artist-image skeleton-image"></div>
      <div class="artist-info">
        <div class="skeleton-title"></div>
        <div class="skeleton-meta"></div>
      </div>
    </div>

    <!-- Actions skeleton -->
    <div class="artist-actions">
      <div class="skeleton-buttons"></div>
    </div>

    <!-- Tracks section skeleton -->
    <section class="section">
      <div class="skeleton-section-title"></div>
      <div class="track-list">
        <TrackSkeleton v-for="i in 8" :key="i" />
      </div>
    </section>
  </div>

  <!-- Actual content -->
  <div class="artist-detail-view" v-else-if="artist">
    <!-- Artist header -->
    <div class="artist-header">
      <div class="artist-image">
        <img v-if="artist.image_url" :src="getCoverUrl(artist.image_url, CoverSize.LARGE)" :alt="artist.name" />
        <div v-else class="image-placeholder"><User :size="48" /></div>
      </div>
      <div class="artist-info">
        <h1>{{ artist.name }}</h1>
        <p class="meta">
          {{ artist.track_count }} треков • {{ artist.album_count }} альбомов
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="artist-actions">
      <div class="action-buttons" v-if="artist.track_count > 0">
        <button class="action-btn play-btn" @click="playAll">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay" :disabled="isShuffling">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Albums section -->
    <section v-if="artist.albums?.length" class="section">
      <h2>Альбомы</h2>
      <div class="albums-row">
        <div
          v-for="album in artist.albums"
          :key="album.id"
          class="album-card"
          @click="goToAlbum(album)"
          @contextmenu.prevent="openMenu('album', album, 'artist', $event)"
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="getCoverUrl(album.cover_url, CoverSize.MEDIUM)" :alt="album.name" />
            <div v-else class="cover-placeholder"><Disc3 :size="24" /></div>
          </div>
          <div class="album-name">{{ album.name }}</div>
          <div class="album-year" v-if="album.release_date">
            {{ formatYear(album.release_date) }}
          </div>
        </div>
      </div>
    </section>

    <!-- Tracks section with virtual scrolling -->
    <section class="section tracks-section">
      <div class="section-header">
        <h2>Все треки</h2>
        <span v-if="tracksTotal > 0" class="tracks-count">{{ tracksTotal }}</span>
      </div>
      
      <!-- Virtual track list with Spotify-style skeleton loading -->
      <div class="virtual-tracks-container" :style="virtualContainerStyle">
        <VirtualTrackList
          ref="virtualTrackListRef"
          :fetchFn="fetchArtistTracks"
          :pageSize="50"
          :skeletonCount="12"
          :showAlbum="true"
          :showAddToLibrary="isGlobal"
          menuContext="artist"
          @click="handleTrackClick"
          @like="handleLikeTrack"
          @menu="handleTrackMenu"
          @download="handleDirectDownload"
          @addToLibrary="handleAddToLibrary"
          @hdNotice="handleHdNotice"
          @update:total="tracksTotal = $event"
        >
          <template #empty>
            <span class="empty-icon"><Music :size="48" /></span>
            <p>Нет треков</p>
          </template>
        </VirtualTrackList>
      </div>
    </section>
  </div>

  <!-- Not in library - offer to view global -->
  <div v-else-if="notInLibrary" class="not-in-library">
    <div class="not-in-library-content">
      <div class="icon"><User :size="48" /></div>
      <h2>{{ decodeURIComponent(route.params.name) }}</h2>
      <p>Артист не найден в вашей библиотеке</p>
      <button class="primary-btn" @click="goToGlobal">
        <Globe :size="16" /> Посмотреть всю музыку артиста
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, usePlaybackActions } from '@/composables'
import VirtualTrackList from '@/components/VirtualTrackList.vue'
import api, { playerApi } from '@/api/client'
import { User, Disc3, Globe, Music } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

// Universal context menu
const { openMenu } = useContextMenu()

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

// Unified track actions
const { handleDirectDownload, handleHdNotice, handleLikeTrack, handleAddToLibrary } = useTrackActions()

const artist = ref(null)
const loading = ref(true)
const notInLibrary = ref(false)
const tracksTotal = ref(0)
const virtualTrackListRef = ref(null)

// Get scope from query param
const scope = computed(() => route.query.scope || 'library')
const isGlobal = computed(() => scope.value === 'global')

// Tracks pagination with virtual scroll
const artistName = computed(() => route.params.name ? decodeURIComponent(route.params.name) : null)

// Calculate container height for virtual list (viewport - header)
const virtualContainerStyle = computed(() => ({
  height: 'calc(100vh - 400px)',
  minHeight: '300px'
}))

const fetchArtistTracks = async ({ offset, limit }) => {
  if (!artistName.value) return { items: [], total: 0 }
  
  const response = await api.get(`/artists/${encodeURIComponent(artistName.value)}/tracks`, {
    params: { offset, limit, scope: scope.value }
  })
  return response.data
}

const loadArtist = async () => {
  loading.value = true
  notInLibrary.value = false
  try {
    const name = decodeURIComponent(route.params.name)
    const params = { scope: scope.value }
    // Use the lightweight /info endpoint (no tracks loaded here)
    const response = await api.get(`/artists/${encodeURIComponent(name)}/info`, { params })
    artist.value = response.data
    // Reset virtual track list
    if (virtualTrackListRef.value) {
      virtualTrackListRef.value.reset()
    }
  } catch (error) {
    // If artist not found in library, show option to view global
    if (error.response?.status === 404 && !isGlobal.value) {
      notInLibrary.value = true
      artist.value = null
    } else {
      console.error('Failed to load artist:', error)
    }
  } finally {
    loading.value = false
  }
}

// Handle track click from VirtualTrackList
const handleTrackClick = ({ track, index, allTracks }) => {
  playerStore.playTracks(allTracks, index)
}

// Handle track menu from VirtualTrackList
const handleTrackMenu = ({ track, index, event }) => {
  openMenu('track', track, 'artist', event)
}

// Unified playback actions - use shufflePlayFull for lazy loading all artist tracks
const { playAll, shufflePlayFull, isShuffling } = usePlaybackActions(() => 
  virtualTrackListRef.value?.getLoadedTracks() || []
)

// Shuffle play handler using lazy loading
const shufflePlay = () => {
  if (artistName.value) {
    shufflePlayFull('artist', artistName.value)
  }
}

const goToAlbum = (album) => {
  const query = isGlobal.value ? { scope: 'global' } : {}
  router.push({ path: `/album/${album.id}`, query })
}

// Go to global scope (used when artist not in library)
const goToGlobal = () => {
  router.push({ 
    path: route.path, 
    query: { scope: 'global' } 
  })
}

// Track actions (handleLikeTrack, handleAddToLibrary, handleDirectDownload, handleHdNotice) 
// are provided by useTrackActions composable above

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatYear = (date) => {
  if (!date) return ''
  return new Date(date).getFullYear()
}

onMounted(() => {
  loadArtist()
})

// Reload when scope changes
watch(scope, () => {
  loadArtist()
})

// Reload when route params change (for sidebar navigation)
watch(
  () => route.params.name,
  (newName, oldName) => {
    if (newName && newName !== oldName) {
      loadArtist()
    }
  }
)
</script>

<style scoped>
.artist-detail-view {
  padding: 16px;
}

.not-in-library {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 16px;
}

.not-in-library-content {
  text-align: center;
}

.not-in-library-content .icon {
  font-size: 80px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.not-in-library-content h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.not-in-library-content p {
  color: var(--text-secondary);
  margin: 0 0 24px 0;
}

.not-in-library-content .primary-btn {
  background: var(--accent-color);
  color: var(--accent-text, #000);
  border: none;
  border-radius: 24px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, opacity 0.2s;
}

.not-in-library-content .primary-btn:hover {
  opacity: 0.9;
  transform: scale(1.02);
}

.artist-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.artist-image {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.artist-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.artist-image .image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 56px;
}

.artist-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.artist-info h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.meta {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.artist-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}

.action-buttons {
  display: flex;
  border-radius: 28px;
  background: var(--accent);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -3px -3px 8px rgba(255, 255, 255, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.action-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #000;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.action-btn::after {
  content: '';
  position: absolute;
  top: 10px;
  bottom: 10px;
  width: 1px;
  background: rgba(0, 0, 0, 0.15);
}

.action-btn.play-btn::after {
  right: 0;
}

.action-btn.shuffle-btn::after {
  display: none;
}

.action-btn:active {
  background: rgba(0, 0, 0, 0.1);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.15);
}

.action-btn.play-btn svg {
  margin-left: 2px;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.albums-row {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
  -webkit-overflow-scrolling: touch;
}

.albums-row::-webkit-scrollbar {
  height: 4px;
}

.albums-row::-webkit-scrollbar-thumb {
  background: var(--bg-highlight);
  border-radius: 2px;
}

.album-card {
  flex-shrink: 0;
  width: 140px;
  cursor: pointer;
}

.album-cover {
  width: 140px;
  height: 140px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 8px;
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
}

.album-name {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-year {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* Tracks section */
.tracks-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.section-header h2 {
  margin: 0;
}

.tracks-count {
  color: var(--text-tertiary);
  font-size: 14px;
  font-weight: 500;
}

.virtual-tracks-container {
  flex: 1;
  min-height: 0;
  border-radius: var(--neu-radius-md, 12px);
  overflow: hidden;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* load-trigger, loading-more are in design-system.css */

.loading-more-tracks {
  margin-top: 8px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px;
}

/* spinner is in design-system.css */

/* Page skeleton styles */
.skeleton-image {
  background: var(--xm-bg-surface, #222);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-title {
  height: 28px;
  width: 180px;
  background: var(--xm-bg-surface, #222);
  border-radius: 4px;
  margin-bottom: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-meta {
  height: 16px;
  width: 140px;
  background: var(--xm-bg-surface, #222);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.1s;
}

.skeleton-buttons {
  width: 100px;
  height: 48px;
  background: var(--xm-bg-surface, #222);
  border-radius: 24px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.2s;
}

.skeleton-section-title {
  height: 20px;
  width: 100px;
  background: var(--xm-bg-surface, #222);
  border-radius: 4px;
  margin-bottom: 16px;
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.3s;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.8;
  }
}
</style>
