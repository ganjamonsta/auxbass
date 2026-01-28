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
      <button class="play-all-btn" @click="playAll" :disabled="!playlist.tracks?.length">
        <span>▶</span>
        Слушать
      </button>
      <button class="shuffle-btn" @click="shufflePlay" :disabled="!playlist.tracks?.length">
        🔀
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
      <TrackItem
        v-for="(track, index) in playlist.tracks"
        :key="track.id"
        :track="track"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="track.is_liked"
        @click="playTrack(track, index)"
        @like="handleLikeTrack(track)"
        @menu="openTrackMenu(track)"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="empty-icon">🎵</span>
      <p>Плейлист пуст</p>
      <p class="hint">Добавляйте треки из библиотеки</p>
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
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const libraryStore = useLibraryStore()

const playlist = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const showDeleteConfirm = ref(false)
const editName = ref('')
const editIsPublic = ref(false)
const showMenu = ref(false)
const menuTrack = ref(null)

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
    await api.delete(`/playlists/${playlist.value.id}`)
    router.push('/playlists')
  } catch (error) {
    console.error('Failed to delete playlist:', error)
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

.play-all-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 32px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.play-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.shuffle-btn,
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

.shuffle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.track-list {
  display: flex;
  flex-direction: column;
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
  gap: 10px;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--accent);
}

.hint-text {
  font-size: 12px;
  color: var(--text-tertiary);
  margin: 0 0 16px 0;
}
</style>
