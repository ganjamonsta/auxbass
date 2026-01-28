<template>
  <div class="playlist-detail-view" v-if="playlist">
    <!-- Playlist header -->
    <div class="playlist-header">
      <div class="playlist-cover">
        <div class="cover-grid" v-if="coverImages.length">
          <img
            v-for="(cover, i) in coverImages"
            :key="i"
            :src="cover"
          />
        </div>
        <div v-else class="cover-placeholder">🎵</div>
      </div>
      <div class="playlist-info">
        <h1>{{ playlist.name }}</h1>
        <p class="meta">
          {{ playlist.track_count }} треков
          <span v-if="playlist.is_public" class="public-badge">🌐 Публичный</span>
        </p>
        <p v-if="playlist.owner_name && !isOwner" class="owner-info">
          от {{ playlist.owner_name }}
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="playlist-actions">
      <div class="action-buttons" v-if="playlist.tracks?.length">
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
      <button v-if="isOwner" class="add-tracks-btn" @click="showAddTracksModal = true">
        ➕ Добавить
      </button>
      <button v-if="isOwner" class="edit-btn" @click="openEditModal">
        ✏️
      </button>
      <button v-if="isOwner" class="delete-btn" @click="showDeleteConfirm = true">
        🗑️
      </button>
    </div>

    <!-- Track list -->
    <div class="track-list" v-if="playlist.tracks?.length">
      <div
        v-for="(track, index) in playlist.tracks"
        :key="track.id"
        class="draggable-track"
        :class="{ 'is-dragging': dragIndex === index, 'drag-over': dragOverIndex === index }"
        :draggable="isOwner"
        @dragstart="handleDragStart($event, index)"
        @dragend="handleDragEnd"
        @dragover.prevent="handleDragOver($event, index)"
        @drop="handleDrop($event, index)"
      >
        <div v-if="isOwner" class="drag-handle">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 15h18v-2H3v2zm0 4h18v-2H3v2zm0-8h18V9H3v2zm0-6v2h18V5H3z"/>
          </svg>
        </div>
        <TrackItem
          :track="track"
          :isPlaying="playerStore.currentTrack?.id === track.id"
          :isLiked="track.is_liked"
          @click="playTrack(track, index)"
          @like="handleLikeTrack(track)"
          @menu="openTrackMenu(track)"
          @download="handleDirectDownload(track)"
        />
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="empty-icon">🎵</span>
      <p>Плейлист пуст</p>
      <p class="hint">Нажмите «Добавить» чтобы добавить треки</p>
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      :inPlaylist="true"
      context="playlist"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
      @addToPlaylist="handleAddToPlaylist"
      @download="handleDownloadTrack"
      @removeFromPlaylist="handleRemoveFromPlaylist"
    />
    
    <!-- Playlist picker modal -->
    <PlaylistPicker
      :show="showPlaylistPickerForMenu"
      :track="menuTrack"
      @close="showPlaylistPickerForMenu = false; closeMenu()"
      @createNew="showPlaylistPickerForMenu = false; closeMenu()"
      @added="handlePlaylistAdded"
    />

    <!-- Edit modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal">
        <h2>Редактировать плейлист</h2>
        <input
          v-model="editName"
          type="text"
          placeholder="Название плейлиста"
          @keyup.enter="savePlaylist"
        />
        <label class="checkbox-label">
          <input type="checkbox" v-model="editIsPublic" />
          <span>Публичный плейлист</span>
        </label>
        <p class="hint-text">Публичные плейлисты видны другим пользователям</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showEditModal = false">Отмена</button>
          <button 
            class="confirm-btn" 
            @click="savePlaylist"
            :disabled="!editName.trim()"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal">
        <h2>Удалить плейлист?</h2>
        <p>Вы уверены, что хотите удалить "{{ playlist.name }}"?</p>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showDeleteConfirm = false">Отмена</button>
          <button class="delete-confirm-btn" @click="deletePlaylist">
            Удалить
          </button>
        </div>
      </div>
    </div>

    <!-- Add tracks modal -->
    <div v-if="showAddTracksModal" class="modal-overlay" @click.self="closeAddTracksModal">
      <div class="modal add-tracks-modal">
        <h2>Добавить треки</h2>
        <div class="search-input-wrapper">
          <input
            v-model="trackSearchQuery"
            type="text"
            placeholder="Поиск треков..."
            @input="debouncedTrackSearch"
            ref="trackSearchInput"
          />
          <div v-if="searchingTracks" class="search-spinner"></div>
        </div>
        
        <div class="search-results" v-if="searchResults.length">
          <div 
            v-for="track in searchResults" 
            :key="track.id" 
            class="search-result-item"
            :class="{ 
              'already-added': isTrackInPlaylist(track.id),
              'is-playing': playerStore.currentTrack?.id === track.id
            }"
          >
            <!-- Cover with Play/Pause overlay -->
            <div class="result-cover-wrapper" @click.stop="togglePreviewPlay(track)">
              <div class="result-cover">
                <img v-if="track.cover_url" :src="track.cover_url" />
                <span v-else>🎵</span>
              </div>
              <div class="cover-play-overlay" :class="{ 'is-playing': playerStore.currentTrack?.id === track.id && playerStore.isPlaying }">
                <svg v-if="playerStore.currentTrack?.id === track.id && playerStore.isPlaying" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8 5v14l11-7z"/>
                </svg>
              </div>
            </div>
            <!-- Track info with progress bar -->
            <div class="result-content">
              <div class="result-info">
                <div class="result-artist">{{ track.artist }}</div>
                <div class="result-title">{{ track.title }}</div>
              </div>
              <!-- Progress bar spanning full width -->
              <div 
                v-if="playerStore.currentTrack?.id === track.id" 
                class="result-progress"
                @click="seekProgress($event, track)"
                @mousedown="startDrag($event, track)"
              >
                <div 
                  class="result-progress-fill" 
                  :style="{ width: `${(playerStore.progress / playerStore.duration) * 100 || 0}%` }"
                ></div>
                <div 
                  class="result-progress-thumb"
                  :style="{ left: `${(playerStore.progress / playerStore.duration) * 100 || 0}%` }"
                ></div>
              </div>
            </div>
            <!-- Duration / Current time -->
            <div class="result-time">
              <template v-if="playerStore.currentTrack?.id === track.id">
                {{ formatTime(playerStore.progress) }}
              </template>
              <template v-else>
                {{ formatTime(track.duration) }}
              </template>
            </div>
            <button 
              v-if="!isTrackInPlaylist(track.id)"
              class="add-track-btn"
              @click="addTrackToPlaylist(track)"
              :disabled="addingTrackId === track.id"
            >
              <span v-if="addingTrackId === track.id">...</span>
              <span v-else>+</span>
            </button>
            <button 
              v-else
              class="remove-track-btn"
              @click="removeTrackFromPlaylistModal(track)"
              :disabled="removingTrackId === track.id"
              title="Удалить из плейлиста"
            >
              <span v-if="removingTrackId === track.id">...</span>
              <span v-else>✓</span>
            </button>
          </div>
        </div>
        
        <div v-else-if="trackSearchQuery && !searchingTracks" class="no-results">
          Ничего не найдено
        </div>
        
        <div v-else class="search-hint">
          Введите название трека или артиста
        </div>
        
        <div class="modal-actions">
          <button class="confirm-btn" @click="closeAddTracksModal">
            Готово
          </button>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import PlaylistPicker from '@/components/PlaylistPicker.vue'
import api, { playerApi } from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

const playlist = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const showDeleteConfirm = ref(false)
const editName = ref('')
const editIsPublic = ref(false)
const showMenu = ref(false)
const menuTrack = ref(null)

// Add tracks modal state
const showAddTracksModal = ref(false)
const trackSearchQuery = ref('')
const searchResults = ref([])
const searchingTracks = ref(false)
const addingTrackId = ref(null)
const removingTrackId = ref(null)
const trackSearchInput = ref(null)
let searchTimeout = null

// Drag and drop state
const dragIndex = ref(null)
const dragOverIndex = ref(null)

const isOwner = computed(() => {
  if (!playlist.value || !authStore.user) return true
  return playlist.value.owner_id === authStore.user.id || !playlist.value.owner_id
})

const coverImages = computed(() => {
  if (!playlist.value?.tracks) return []
  const covers = playlist.value.tracks
    .filter(t => t.cover_url)
    .slice(0, 4)
    .map(t => t.cover_url)
  return covers
})

const loadPlaylist = async () => {
  loading.value = true
  try {
    const response = await api.get(`/playlists/${route.params.id}`)
    playlist.value = response.data
    editName.value = playlist.value.name
    editIsPublic.value = playlist.value.is_public || false
  } finally {
    loading.value = false
  }
}

const openEditModal = () => {
  editName.value = playlist.value.name
  editIsPublic.value = playlist.value.is_public || false
  showEditModal.value = true
}

const playAll = () => {
  if (playlist.value?.tracks?.length) {
    playerStore.playTrack(playlist.value.tracks[0], playlist.value.tracks)
  }
}

const shufflePlay = () => {
  if (playlist.value?.tracks?.length) {
    const shuffled = [...playlist.value.tracks].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, playlist.value.tracks, index)
}

const removeTrack = async (track) => {
  try {
    await api.delete(`/playlists/${playlist.value.id}/tracks/${track.id}`)
    playlist.value.tracks = playlist.value.tracks.filter(t => t.id !== track.id)
    playlist.value.track_count--
  } catch (error) {
    console.error('Failed to remove track:', error)
  }
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

const handleGoToArtist = () => {
  closeMenu()
  router.push(`/artist/${encodeURIComponent(menuTrack.value?.artist)}`)
}

const handleGoToAlbum = () => {
  closeMenu()
  const albumId = menuTrack.value?.album?.id || menuTrack.value?.album_id
  if (albumId) {
    router.push(`/album/${albumId}`)
  }
}

const handleAddToPlaylist = () => {
  showPlaylistPickerForMenu.value = true
}

const showPlaylistPickerForMenu = ref(false)
const handlePlaylistAdded = (playlist) => {
  uiStore.toast.success('Добавлено', `Трек добавлен в плейлист "${playlist.name}"`)
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
  try {
    await playerApi.download(track.id)
    uiStore.toast.success('Трек отправлен', 'Проверьте сообщения в Telegram')
  } catch (error) {
    console.error('Failed to download track:', error)
    const errorMsg = error.response?.data?.detail || 'Ошибка отправки'
    uiStore.toast.error('Не удалось отправить', errorMsg)
  }
}

const handleRemoveFromPlaylist = async () => {
  if (!menuTrack.value) return
  await removeTrack(menuTrack.value)
  closeMenu()
}

const savePlaylist = async () => {
  if (!editName.value.trim()) return
  
  try {
    await api.put(`/playlists/${playlist.value.id}`, {
      name: editName.value.trim(),
      is_public: editIsPublic.value
    })
    playlist.value.name = editName.value.trim()
    playlist.value.is_public = editIsPublic.value
    showEditModal.value = false
  } catch (error) {
    console.error('Failed to update playlist:', error)
  }
}

const deletePlaylist = async () => {
  try {
    const playlistId = playlist.value.id
    await api.delete(`/playlists/${playlistId}`)
    // Update library store to remove playlist from cache
    await libraryStore.deletePlaylist(playlistId)
    uiStore.toast.success('Удалено', 'Плейлист удален')
    router.push('/playlists')
  } catch (error) {
    console.error('Failed to delete playlist:', error)
    uiStore.toast.error('Ошибка', 'Не удалось удалить плейлист')
  }
}

// Add tracks modal functions
const isTrackInPlaylist = (trackId) => {
  return playlist.value?.tracks?.some(t => t.id === trackId) || false
}

const closeAddTracksModal = () => {
  showAddTracksModal.value = false
  trackSearchQuery.value = ''
  searchResults.value = []
}

const debouncedTrackSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    searchTracks()
  }, 300)
}

const searchTracks = async () => {
  if (!trackSearchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  searchingTracks.value = true
  try {
    // Search in personal library first
    const libraryResponse = await api.get('/library', {
      params: {
        search: trackSearchQuery.value,
        per_page: 20
      }
    })
    const libraryTracks = libraryResponse.data.items || []
    
    // Then search in global library
    const globalResponse = await api.get('/tracks/global', {
      params: {
        search: trackSearchQuery.value,
        per_page: 20
      }
    })
    const globalTracks = globalResponse.data.items || []
    
    // Merge results, avoiding duplicates (by track id)
    const seenIds = new Set(libraryTracks.map(t => t.id))
    const uniqueGlobalTracks = globalTracks.filter(t => !seenIds.has(t.id))
    
    searchResults.value = [...libraryTracks, ...uniqueGlobalTracks].slice(0, 30)
  } catch (error) {
    console.error('Failed to search tracks:', error)
    searchResults.value = []
  } finally {
    searchingTracks.value = false
  }
}

const addTrackToPlaylist = async (track) => {
  if (addingTrackId.value) return
  
  addingTrackId.value = track.id
  try {
    await api.post(`/playlists/${playlist.value.id}/tracks`, {
      track_id: track.id
    })
    // Add track to local playlist
    if (!playlist.value.tracks) {
      playlist.value.tracks = []
    }
    playlist.value.tracks.push(track)
    playlist.value.track_count = (playlist.value.track_count || 0) + 1
  } catch (error) {
    console.error('Failed to add track:', error)
  } finally {
    addingTrackId.value = null
  }
}

const removeTrackFromPlaylistModal = async (track) => {
  if (removingTrackId.value) return
  
  removingTrackId.value = track.id
  try {
    await api.delete(`/playlists/${playlist.value.id}/tracks/${track.id}`)
    // Remove track from local playlist
    playlist.value.tracks = playlist.value.tracks.filter(t => t.id !== track.id)
    playlist.value.track_count = Math.max(0, (playlist.value.track_count || 1) - 1)
  } catch (error) {
    console.error('Failed to remove track:', error)
  } finally {
    removingTrackId.value = null
  }
}

// Preview play/pause for track selection
const togglePreviewPlay = (track) => {
  if (playerStore.currentTrack?.id === track.id) {
    // Toggle play/pause for current track
    playerStore.togglePlay()
  } else {
    // Play new track (use search results as queue for preview)
    playerStore.playTrack(track, searchResults.value)
  }
}

// Format time in MM:SS
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// Seek progress bar
const seekProgress = (event, track) => {
  if (playerStore.currentTrack?.id !== track.id) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width))
  const newTime = percent * playerStore.duration
  playerStore.seek(newTime)
}

// Drag handling for progress bar
let isDragging = false
const startDrag = (event, track) => {
  if (playerStore.currentTrack?.id !== track.id) return
  isDragging = true
  
  const onMouseMove = (e) => {
    if (!isDragging) return
    const progressBar = event.currentTarget
    const rect = progressBar.getBoundingClientRect()
    const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    const newTime = percent * playerStore.duration
    playerStore.seek(newTime)
  }
  
  const onMouseUp = () => {
    isDragging = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// Drag and drop functions
const handleDragStart = (event, index) => {
  dragIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', index.toString())
}

const handleDragEnd = () => {
  dragIndex.value = null
  dragOverIndex.value = null
}

const handleDragOver = (event, index) => {
  event.preventDefault()
  dragOverIndex.value = index
}

const handleDrop = async (event, toIndex) => {
  event.preventDefault()
  const fromIndex = dragIndex.value
  
  if (fromIndex === null || fromIndex === toIndex) {
    handleDragEnd()
    return
  }
  
  // Reorder locally first
  const tracks = [...playlist.value.tracks]
  const [movedTrack] = tracks.splice(fromIndex, 1)
  tracks.splice(toIndex, 0, movedTrack)
  playlist.value.tracks = tracks
  
  handleDragEnd()
  
  // Send to server
  try {
    await api.put(`/playlists/${playlist.value.id}/reorder`, {
      track_ids: tracks.map(t => t.id)
    })
  } catch (error) {
    console.error('Failed to reorder tracks:', error)
    // Reload playlist on error
    loadPlaylist()
  }
}

onMounted(() => {
  loadPlaylist()
})
</script>

<style scoped>
.playlist-detail-view {
  padding: 16px;
  padding-bottom: 120px;
}

.playlist-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.playlist-cover {
  width: 140px;
  height: 140px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.cover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  width: 100%;
  height: 100%;
}

.cover-grid img {
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
  font-size: 48px;
}

.playlist-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.playlist-info h1 {
  font-size: 24px;
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

.playlist-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
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

.edit-btn,
.delete-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  font-size: 18px;
  cursor: pointer;
}

.track-list {
  display: flex;
  flex-direction: column;
}

/* Ensure track items fill width */
.track-list :deep(.track-item) {
  flex: 1;
  margin-right: 0;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.hint {
  color: var(--text-tertiary);
  font-size: 14px;
  margin-top: 8px;
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

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal {
  background: var(--bg-elevated);
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}

.modal h2 {
  margin: 0 0 16px 0;
  font-size: 20px;
  color: var(--text-primary);
}

.modal p {
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.modal input {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 16px;
  margin-bottom: 20px;
}

.modal input::placeholder {
  color: var(--text-tertiary);
}

.modal input:focus {
  outline: none;
  border-color: var(--accent);
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn {
  flex: 1;
  padding: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
}

.confirm-btn {
  flex: 1;
  padding: 12px;
  background: var(--accent);
  border: none;
  border-radius: 10px;
  color: #000;
  font-weight: 600;
  cursor: pointer;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-confirm-btn {
  flex: 1;
  padding: 12px;
  background: var(--danger);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.public-badge {
  display: inline-block;
  margin-left: 8px;
  font-size: 12px;
  color: var(--accent);
}

.owner-info {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 44px;
  height: 24px;
  background: var(--bg-highlight);
  border-radius: 12px;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}

.checkbox-label input[type="checkbox"]::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.checkbox-label input[type="checkbox"]:checked {
  background: var(--accent);
}

.checkbox-label input[type="checkbox"]:checked::before {
  transform: translateX(20px);
}

.hint-text {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 16px 0;
}

/* Add tracks button */
.add-tracks-btn {
  padding: 10px 16px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color, rgba(255,255,255,0.1));
  border-radius: 20px;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-tracks-btn:hover {
  background: var(--bg-highlight);
}

/* Add tracks modal */
.add-tracks-modal {
  height: 70vh;
  max-height: 600px;
  min-height: 400px;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
}

/* Desktop: wider modal */
@media (min-width: 768px) {
  .add-tracks-modal {
    max-width: 550px;
    height: 75vh;
    max-height: 700px;
  }
}

.search-input-wrapper {
  position: relative;
  margin-bottom: 16px;
}

.search-input-wrapper input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 15px;
}

.search-input-wrapper input::placeholder {
  color: var(--text-tertiary);
}

.search-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  border: 2px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.search-results {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  margin-bottom: 16px;
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  transition: background 0.2s;
}

.search-result-item:hover {
  background: var(--bg-elevated);
}

.search-result-item.already-added {
  opacity: 0.6;
}

.search-result-item.is-playing {
  background: rgba(29, 185, 84, 0.1);
}

/* Cover wrapper with play overlay */
.result-cover-wrapper {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
}

.result-cover-wrapper:hover .cover-play-overlay {
  opacity: 1;
}

.result-cover-wrapper:hover .result-cover img {
  filter: brightness(0.6);
}

.result-cover {
  width: 100%;
  height: 100%;
  background: var(--bg-highlight);
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: filter 0.2s;
}

.cover-play-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s;
  color: #fff;
}

.cover-play-overlay.is-playing {
  opacity: 1;
  background: rgba(0, 0, 0, 0.3);
}

/* Track content with info and progress */
.result-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.result-title {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.result-artist {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Progress bar spanning full width */
.result-progress {
  position: relative;
  width: 100%;
  height: 12px;
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 4px 0;
}

.result-progress::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

.result-progress-fill {
  position: absolute;
  left: 0;
  height: 3px;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.05s linear;
  pointer-events: none;
}

.result-progress-thumb {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--accent);
  border-radius: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.15s;
  pointer-events: none;
}

.result-progress:hover .result-progress-thumb,
.result-progress:active .result-progress-thumb {
  opacity: 1;
}

.result-time {
  font-size: 13px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
  min-width: 40px;
  text-align: right;
}

.search-result-item.is-playing .result-time {
  color: var(--accent);
}

.add-track-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.add-track-btn:hover {
  transform: scale(1.1);
}

.add-track-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.remove-track-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.remove-track-btn:hover {
  background: var(--danger, #e53935);
  color: #fff;
}

.remove-track-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.no-results, .search-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 32px 16px;
  color: var(--text-tertiary);
  min-height: 200px;
}

/* Drag and drop styles */
.draggable-track {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
  transition: background 0.2s, transform 0.15s;
}

.draggable-track :deep(.track-item) {
  flex: 1;
  min-width: 0;
}

.draggable-track:hover {
  background: var(--bg-elevated);
}

.draggable-track.is-dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.draggable-track.drag-over {
  background: var(--bg-highlight);
}

.draggable-track.drag-over::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent);
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 44px;
  cursor: grab;
  color: var(--text-tertiary);
  flex-shrink: 0;
  transition: color 0.2s;
}

.drag-handle:hover {
  color: var(--text-secondary);
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle svg {
  width: 16px;
  height: 16px;
}

@keyframes spin {
  to { transform: translateY(-50%) rotate(360deg); }
}
</style>
