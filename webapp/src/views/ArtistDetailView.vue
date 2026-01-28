<template>
  <div class="artist-detail-view" v-if="artist">
    <!-- Artist header -->
    <div class="artist-header">
      <div class="artist-image">
        <img v-if="artist.image_url" :src="artist.image_url" :alt="artist.name" />
        <div v-else class="image-placeholder">👤</div>
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
      <div class="action-buttons" v-if="artist.tracks?.length">
        <button class="action-btn play-btn" @click="playAll">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay">
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
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
            <div v-else class="cover-placeholder">💿</div>
          </div>
          <div class="album-name">{{ album.name }}</div>
          <div class="album-year" v-if="album.release_date">
            {{ formatYear(album.release_date) }}
          </div>
        </div>
      </div>
    </section>

    <!-- Tracks section -->
    <section class="section">
      <h2>Все треки</h2>
      <div class="track-list">
        <TrackItem
          v-for="(track, index) in artist.tracks"
          :key="track.id"
          :track="track"
          :isPlaying="playerStore.currentTrack?.id === track.id"
          :isLiked="track.is_liked"
          :showAlbum="true"
          :showAddToLibrary="isGlobal"
          :inLibrary="track.in_library"
          @click="playTrack(track, index)"
          @like="handleLikeTrack(track)"
          @addToLibrary="handleAddToLibrary(track)"
          @menu="openTrackMenu(track)"
          @download="handleDirectDownload(track)"
        />
      </div>
    </section>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      context="artist"
      @close="closeMenu"
      @goToAlbum="handleGoToAlbum"
      @addToPlaylist="handleAddToPlaylist"
      @download="handleDownloadTrack"
    />
  </div>

  <!-- Not in library - offer to view global -->
  <div v-else-if="notInLibrary" class="not-in-library">
    <div class="not-in-library-content">
      <div class="icon">👤</div>
      <h2>{{ decodeURIComponent(route.params.name) }}</h2>
      <p>Артист не найден в вашей библиотеке</p>
      <button class="primary-btn" @click="goToGlobal">
        🌍 Посмотреть всю музыку артиста
      </button>
    </div>
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()

const artist = ref(null)
const loading = ref(true)
const showMenu = ref(false)
const menuTrack = ref(null)
const notInLibrary = ref(false)

// Get scope from query param
const scope = computed(() => route.query.scope || 'library')
const isGlobal = computed(() => scope.value === 'global')

const loadArtist = async () => {
  loading.value = true
  notInLibrary.value = false
  try {
    const name = decodeURIComponent(route.params.name)
    const params = { scope: scope.value }
    const response = await api.get(`/artists/${encodeURIComponent(name)}`, { params })
    artist.value = response.data
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

const playAll = () => {
  if (artist.value?.tracks?.length) {
    playerStore.playTrack(artist.value.tracks[0], artist.value.tracks)
  }
}

const shufflePlay = () => {
  if (artist.value?.tracks?.length) {
    const shuffled = [...artist.value.tracks].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, artist.value.tracks, index)
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

// Track menu handlers
const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

const handleLikeTrack = async (track) => {
  const newLikedState = await libraryStore.toggleLike(track.id)
  track.is_liked = newLikedState
}

const handleAddToLibrary = async (track) => {
  const success = await libraryStore.addToLibrary(track.id)
  if (success) {
    track.in_library = true
  }
}

const handleGoToAlbum = () => {
  closeMenu()
  const albumId = menuTrack.value?.album?.id || menuTrack.value?.album_id
  if (albumId) {
    router.push(`/album/${albumId}`)
  }
}

const handleAddToPlaylist = () => {
  closeMenu()
  // TODO: implement playlist picker
}

const handleDownloadTrack = async () => {
  if (!menuTrack.value) return
  try {
    const response = await api.get(`/player/stream/${menuTrack.value.id}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${menuTrack.value.artist} - ${menuTrack.value.title}.mp3`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download:', error)
  }
  closeMenu()
}

// Handle direct download from TrackItem (for large/HD files)
const handleDirectDownload = async (track) => {
  const isLargeFile = track.file_size && track.file_size > 20 * 1024 * 1024
  const hdMimeTypes = ['audio/flac', 'audio/x-flac', 'audio/wav', 'audio/x-wav', 'audio/aiff', 'audio/x-aiff']
  const isHd = track.mime_type && hdMimeTypes.includes(track.mime_type.toLowerCase())
  
  if (isLargeFile || isHd) {
    alert('Файл слишком большой для скачивания через браузер. Используйте Telegram бота для скачивания.')
    return
  }
  
  try {
    const response = await api.get(`/player/stream/${track.id}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${track.artist} - ${track.title}.mp3`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download:', error)
    alert('Ошибка при скачивании. Попробуйте через Telegram бота.')
  }
}

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
</script>

<style scoped>
.artist-detail-view {
  padding: 16px;
  padding-bottom: 120px;
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
  color: white;
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

.track-list {
  display: flex;
  flex-direction: column;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
