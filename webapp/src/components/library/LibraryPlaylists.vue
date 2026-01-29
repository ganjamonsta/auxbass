<template>
  <div class="library-playlists">
    <!-- Header with create button (if needed, or just keep it floating/top) -->
    <div class="actions-header">
       <div class="liked-quick-access" @click="goToLiked">
        <div class="liked-icon">❤️</div>
        <span>Любимое ({{ likedCount }})</span>
      </div>
      <button class="create-btn" @click="showCreateModal = true">
        ➕ Создать
      </button>
    </div>

    <!-- Playlists grid -->
    <div class="playlists-grid" v-if="playlists.length">
        <!-- Liked tracks special card - maybe redundant if we have quick access above, but consistent with PlaylistsView -->
        <!-- Actually I moved liked card to `actions-header` or keep it in grid? -->
        <!-- PlaylistsView has it as a special card. Let's keep consistency. -->
      <div class="playlist-card liked-card" @click="goToLiked">
        <div class="playlist-cover liked-cover">
          <span class="liked-icon">❤️</span>
        </div>
        <div class="playlist-name">Понравившиеся</div>
        <div class="playlist-meta">{{ likedCount }} треков</div>
      </div>

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
      <h3 v-if="searchQuery">Плейлисты не найдены</h3>
      <template v-else>
         <p>У вас пока нет плейлистов</p>
         <button class="create-first-btn" @click="showCreateModal = true">
            Создать плейлист
         </button>
      </template>
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
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import api from '@/api/client'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const libraryStore = useLibraryStore()

const playlists = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const nameInput = ref(null)
const likedCount = ref(0)
const fullPlaylists = ref([]) // Store full list for local search if needed

const loadPlaylists = async () => {
    loading.value = true
    try {
        // Fetch liked count
        const likedRes = await api.get('/tracks/liked') 
        likedCount.value = likedRes.data.total
        
        await libraryStore.fetchPlaylists() // Populates libraryStore.playlists
        playlists.value = libraryStore.playlists
        fullPlaylists.value = libraryStore.playlists 
        
        // Filter if query exists
        if (props.searchQuery) {
            playlists.value = fullPlaylists.value.filter(p => p.name.toLowerCase().includes(props.searchQuery.toLowerCase()))
        }
        
    } finally {
        loading.value = false
    }
}

watch(() => props.searchQuery, (query) => {
    if (!query) {
        playlists.value = fullPlaylists.value
    } else {
        playlists.value = fullPlaylists.value.filter(p => p.name.toLowerCase().includes(query.toLowerCase()))
    }
})

const createPlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  
  try {
    const response = await api.post('/playlists', {
      name: newPlaylistName.value
    })
    
    closeModal()
    loadPlaylists() // Reload
    // Optionally push to router? No, stay here.
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

const closeModal = () => {
  showCreateModal.value = false
  newPlaylistName.value = ''
}

const goToPlaylist = (playlist) => {
  router.push(`/playlist/${playlist.id}`)
}

const goToLiked = () => {
  router.push('/liked')
}

// Watch for modal open to focus input
watch(showCreateModal, (val) => {
  if (val) {
    nextTick(() => {
      nameInput.value?.focus()
    })
  }
})

onMounted(() => {
  loadPlaylists()
})
</script>

<style scoped>
.library-playlists {
    padding-bottom: 20px;
}
.actions-header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-bottom: 16px;
}

.liked-quick-access {
    display: none; /* Hide in header, show in grid instead */
}

.create-btn {
    padding: 10px 16px;
    background: var(--accent);
    border: none;
    border-radius: 20px;
    color: #000;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
    flex-shrink: 0;
}

.create-btn:hover {
    opacity: 0.9;
}

.create-btn:active {
    transform: scale(0.97);
}

/* Reusing PlaylistsView styles */
.playlists-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (min-width: 400px) {
  .playlists-grid {
    gap: 16px;
  }
}

@media (min-width: 500px) {
  .playlists-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 700px) {
  .playlists-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
}

@media (min-width: 900px) {
  .playlists-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}

.playlist-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.playlist-card:active {
  transform: scale(0.98);
}

.playlist-cover {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 8px;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
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

.liked-card .playlist-cover {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.liked-icon {
  font-size: 40px;
}

.playlist-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.playlist-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

.loading {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Modal styles - should be global? Keeping scoped for safety */
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
  z-index: 100;
}

.modal {
  background: var(--bg-card);
  padding: 24px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
}

.modal h2 {
  margin-top: 0;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.modal input {
  width: 100%;
  padding: 12px;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  margin-bottom: 16px;
  font-size: 16px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal button {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  cursor: pointer;
}

.cancel-btn {
  background: transparent;
  color: var(--text-secondary);
}

.confirm-btn {
  background: var(--accent);
  color: white;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}
</style>
