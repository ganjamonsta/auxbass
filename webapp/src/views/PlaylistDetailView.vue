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
      <div class="action-buttons">
        <button class="action-btn play-btn" @click="playAll" :disabled="!playlist.tracks?.length">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay" :disabled="!playlist.tracks?.length">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>
        <button v-if="isOwner" class="action-btn edit-btn" @click="openEditModal">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Track list -->
    <div class="track-list" v-if="playlist.tracks?.length">
      <div
        v-for="(track, index) in playlist.tracks"
        :key="track.id"
        class="track-wrapper"
      >
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
    <EditPlaylistModal
      :show="showEditModal"
      :playlist="playlist"
      @close="showEditModal = false"
      @save="handleSavePlaylist"
      @delete="showDeleteConfirm = true"
      @update:tracks="handleTracksUpdate"
    />

    <!-- Delete confirm -->
    <ConfirmDialog
      :show="showDeleteConfirm"
      type="danger"
      title="Удалить плейлист?"
      :message="`Вы уверены, что хотите удалить '${playlist?.name}'?`"
      confirmText="Удалить"
      cancelText="Отмена"
      @confirm="deletePlaylist"
      @cancel="showDeleteConfirm = false"
    />
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
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EditPlaylistModal from '@/components/EditPlaylistModal.vue'
import api, { playerApi } from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

// State
const playlist = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const showDeleteConfirm = ref(false)
const showMenu = ref(false)
const menuTrack = ref(null)
const showPlaylistPickerForMenu = ref(false)

// Computed
const isOwner = computed(() => {
  if (!playlist.value || !authStore.user) return true
  return playlist.value.owner_id === authStore.user.id || !playlist.value.owner_id
})

const coverImages = computed(() => {
  if (!playlist.value?.tracks) return []
  return playlist.value.tracks.filter(t => t.cover_url).slice(0, 4).map(t => t.cover_url)
})

// Data loading
const loadPlaylist = async () => {
  loading.value = true
  try {
    const response = await api.get(`/playlists/${route.params.id}`)
    playlist.value = response.data
  } finally {
    loading.value = false
  }
}

// Playback
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

// Track menu
const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

const handleLikeTrack = async (track) => {
  track.is_liked = await libraryStore.toggleLike(track.id)
}

const handleGoToArtist = () => {
  closeMenu()
  router.push(`/artist/${encodeURIComponent(menuTrack.value?.artist)}`)
}

const handleGoToAlbum = () => {
  closeMenu()
  const albumId = menuTrack.value?.album?.id || menuTrack.value?.album_id
  if (albumId) router.push(`/album/${albumId}`)
}

const handleAddToPlaylist = () => {
  showPlaylistPickerForMenu.value = true
}

const handlePlaylistAdded = (pl) => {
  uiStore.toast.success('Добавлено', `Трек добавлен в плейлист "${pl.name}"`)
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

const handleDirectDownload = async (track) => {
  try {
    await playerApi.download(track.id)
    uiStore.toast.success('Трек отправлен', 'Проверьте сообщения в Telegram')
  } catch (error) {
    const errorMsg = error.response?.data?.detail || 'Ошибка отправки'
    uiStore.toast.error('Не удалось отправить', errorMsg)
  }
}

const handleRemoveFromPlaylist = async () => {
  if (!menuTrack.value) return
  try {
    await api.delete(`/playlists/${playlist.value.id}/tracks/${menuTrack.value.id}`)
    playlist.value.tracks = playlist.value.tracks.filter(t => t.id !== menuTrack.value.id)
    playlist.value.track_count--
    // Update track_count in library store
    const libraryPlaylist = libraryStore.playlists.find(p => p.id === playlist.value.id)
    if (libraryPlaylist && libraryPlaylist.track_count > 0) {
      libraryPlaylist.track_count--
    }
  } catch (error) {
    console.error('Failed to remove track:', error)
  }
  closeMenu()
}

// Edit modal handlers
const openEditModal = () => {
  showEditModal.value = true
}

const handleSavePlaylist = ({ name, isPublic }) => {
  playlist.value.name = name
  playlist.value.is_public = isPublic
  // Update in library store
  const libraryPlaylist = libraryStore.playlists.find(p => p.id === playlist.value.id)
  if (libraryPlaylist) {
    libraryPlaylist.name = name
    libraryPlaylist.is_public = isPublic
  }
  showEditModal.value = false
  uiStore.toast.success('Сохранено', 'Плейлист обновлён')
}

const handleTracksUpdate = (tracks) => {
  playlist.value.tracks = tracks
  playlist.value.track_count = tracks.length
  // Update track_count in library store
  const libraryPlaylist = libraryStore.playlists.find(p => p.id === playlist.value.id)
  if (libraryPlaylist) {
    libraryPlaylist.track_count = tracks.length
  }
}

const deletePlaylist = async () => {
  try {
    await api.delete(`/playlists/${playlist.value.id}`)
    await libraryStore.deletePlaylist(playlist.value.id)
    uiStore.toast.success('Удалено', 'Плейлист удален')
    router.push('/playlists')
  } catch (error) {
    console.error('Failed to delete playlist:', error)
    uiStore.toast.error('Ошибка', 'Не удалось удалить плейлист')
  }
}

onMounted(loadPlaylist)
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

.action-btn:active {
  background: rgba(0, 0, 0, 0.1);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.15);
}

.action-btn.play-btn svg {
  margin-left: 2px;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-btn.shuffle-btn::after {
  right: 0;
}

.action-btn.edit-btn::after {
  display: none;
}

/* Hide separator when edit button not shown (not owner) */
.action-buttons:not(:has(.edit-btn)) .shuffle-btn::after {
  display: none;
}

.track-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
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
</style>
