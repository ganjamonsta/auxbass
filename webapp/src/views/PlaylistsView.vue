<template>
  <div class="playlists-view">
    <!-- Header with create button -->
    <div class="header">
      <h1>Плейлисты</h1>
      <button class="create-btn" @click="handleCreatePlaylist">
        <Plus :size="16" /> Создать
      </button>
    </div>

    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск плейлистов..."
    />

    <!-- Loading state with skeletons -->
    <div v-if="loading" class="media-grid type-playlist">
      <!-- Liked card skeleton -->
      <div class="playlist-card liked-card skeleton-liked">
        <div class="playlist-cover liked-cover"></div>
        <div class="skeleton-text"></div>
        <div class="skeleton-meta"></div>
      </div>
      <GridSkeleton v-for="i in 8" :key="i" type="playlist" />
    </div>

    <!-- Playlists grid -->
    <MediaGrid
      v-else
      type="playlist"
      :items="filteredPlaylists"
      :loading="false"
      @click="goToPlaylist"
      @contextmenu="handleContextMenu"
    >
      <template #prepend-grid>
        <!-- Liked tracks special card -->
        <div class="playlist-card liked-card" @click="goToLiked">
          <div class="playlist-cover liked-cover">
            <span class="liked-icon"><Heart :size="24" class="heart-icon" /></span>
          </div>
          <div class="playlist-name">Понравившиеся</div>
          <div class="playlist-meta">{{ likedCount }} треков</div>
        </div>
      </template>

      <template #empty>
         <div class="empty-state">
          <span class="empty-icon"><FileText :size="48" /></span>
          <p>У вас пока нет плейлистов</p>
          <button class="create-first-btn" @click="handleCreatePlaylist">
           Создать плейлист
         </button>
       </div>
      </template>
    </MediaGrid>

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
          <button type="button" class="cancel-btn" @click="closeModal">Отмена</button>
          <button 
            type="button"
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
import { ref, computed, onMounted, onActivated, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useContextMenu } from '@/composables/useContextMenu'
import api from '@/api/client'
import { Plus, Heart, FileText } from 'lucide-vue-next'
import MediaGrid from '@/components/MediaGrid.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import SearchBar from '@/components/ui/SearchBar.vue'

// Universal context menu
const { openMenu } = useContextMenu()

const handleContextMenu = ({ item, event }) => {
  openMenu('playlist', item, 'library', event)
}

const router = useRouter()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()

// Use store for playlists
const playlists = computed(() => libraryStore.playlists)
const loading = ref(false) // libraryStore.loading? maybe better to track locally for this view or use store's
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const nameInput = ref(null)
const likedCount = computed(() => libraryStore.likedTracks?.length || 0)

// Search state
const searchQuery = ref('')

// Filtered playlists
const filteredPlaylists = computed(() => {
  if (!searchQuery.value) {
    return playlists.value
  }
  const query = searchQuery.value.toLowerCase()
  return playlists.value.filter(p => 
    p.name.toLowerCase().includes(query)
  )
})

// Handle create playlist - check for channel
const handleCreatePlaylist = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  showCreateModal.value = true
}

const loadPlaylists = async () => {
  loading.value = true
  try {
    // Force refresh? Or just fetch if empty?
    // Since this is a main view, we might want to ensure we have data.
    if (playlists.value.length === 0) {
      await libraryStore.fetchPlaylists()
    } else {
        // Maybe background refresh?
        libraryStore.fetchPlaylists()
    }
  } finally {
    loading.value = false
  }
}

const loadLikedCount = async () => {
  try {
    if (!libraryStore.likedTracks.length) {
        await libraryStore.fetchLikedTracks()
    }
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
    const newPlaylist = await libraryStore.createPlaylist(newPlaylistName.value.trim())
    if (newPlaylist) {
        closeModal()
        router.push(`/playlist/${newPlaylist.id}`)
    }
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

onMounted(() => {
  loadPlaylists()
  loadLikedCount()
})

// Reload playlists when returning to this view (keep-alive)
onActivated(() => {
  loadPlaylists()
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
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
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
  width: auto !important;
  max-width: fit-content;
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
  font-size: 40px;
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

.cover-grid.single-cover {
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
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
  font-size: 40px;
}

.playlist-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.playlist-meta {
  color: var(--text-tertiary);
  font-size: 11px;
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

/* Skeleton styles */
.skeleton-liked .playlist-cover {
  background: var(--bg-tertiary);
}

.skeleton-text {
  height: 14px;
  width: 80%;
  background: var(--bg-tertiary);
  border-radius: 4px;
  margin-top: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-meta {
  height: 12px;
  width: 50%;
  background: var(--bg-tertiary);
  border-radius: 4px;
  margin-top: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.7; }
}
</style>
