<template>
  <div class="playlists-view">
    <!-- Header with create button -->
    <div class="header">
      <h1>Плейлисты</h1>
      <button class="create-btn" @click="showCreateModal = true">
        ➕ Создать
      </button>
    </div>

    <!-- Liked tracks special card -->
    <div class="special-playlists">
      <div class="playlist-card liked-card" @click="goToLiked">
        <div class="playlist-cover liked-cover">
          <span class="liked-icon">❤️</span>
        </div>
        <div class="playlist-name">Понравившиеся</div>
        <div class="playlist-meta">{{ likedCount }} треков</div>
      </div>
    </div>

    <!-- Playlists grid -->
    <div class="playlists-grid" v-if="playlists.length">
      <div
        v-for="playlist in playlists"
        :key="playlist.id"
        class="playlist-card"
        @click="goToPlaylist(playlist)"
      >
        <div class="playlist-cover">
          <div class="cover-grid" v-if="playlist.covers?.length">
            <img
              v-for="(cover, i) in playlist.covers.slice(0, 4)"
              :key="i"
              :src="cover"
            />
          </div>
          <div v-else class="cover-placeholder">🎵</div>
        </div>
        <div class="playlist-name">{{ playlist.name }}</div>
        <div class="playlist-meta">{{ playlist.track_count }} треков</div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="empty-state">
      <span class="empty-icon">📝</span>
      <p>У вас пока нет плейлистов</p>
      <button class="create-first-btn" @click="showCreateModal = true">
        Создать плейлист
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <h2>Новый плейлист</h2>
        <input
          v-model="newPlaylistName"
          type="text"
          placeholder="Название плейлиста"
          ref="nameInput"
          @keyup.enter="createPlaylist"
        />
        <div class="modal-actions">
          <button class="cancel-btn" @click="closeModal">Отмена</button>
          <button 
            class="confirm-btn" 
            @click="createPlaylist"
            :disabled="!newPlaylistName.trim()"
          >
            Создать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import api from '@/api/client'

const router = useRouter()
const libraryStore = useLibraryStore()

const playlists = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const nameInput = ref(null)
const likedCount = ref(0)

const loadPlaylists = async () => {
  loading.value = true
  try {
    const response = await api.get('/playlists')
    playlists.value = response.data.items || response.data
  } finally {
    loading.value = false
  }
}

const loadLikedCount = async () => {
  try {
    await libraryStore.fetchLikedTracks()
    likedCount.value = libraryStore.likedTracks?.length || 0
  } catch (e) {
    console.error('Failed to load liked count:', e)
  }
}

const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const goToLiked = () => {
  router.push('/liked')
}

const closeModal = () => {
  showCreateModal.value = false
  newPlaylistName.value = ''
}

const createPlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  
  try {
    const response = await api.post('/playlists', {
      name: newPlaylistName.value.trim()
    })
    playlists.value.unshift(response.data)
    closeModal()
    router.push(`/playlist/${response.data.id}`)
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

onMounted(() => {
  loadPlaylists()
  loadLikedCount()
})

// Focus input when modal opens
const openModal = async () => {
  showCreateModal.value = true
  await nextTick()
  nameInput.value?.focus()
}
</script>

<style scoped>
.playlists-view {
  padding: 16px;
  padding-bottom: 120px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.create-btn {
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.special-playlists {
  margin-bottom: 24px;
}

.liked-card {
  display: inline-block;
  cursor: pointer;
  width: 160px;
}

.liked-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4564, #c8325a);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.liked-icon {
  font-size: 48px;
}

.playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
}

.playlist-card {
  cursor: pointer;
}

.playlist-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 10px;
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

.playlist-name {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.playlist-meta {
  color: var(--text-tertiary);
  font-size: 13px;
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

.create-first-btn {
  margin-top: 16px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
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
  margin: 0 0 20px 0;
  font-size: 20px;
  color: var(--text-primary);
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
</style>
