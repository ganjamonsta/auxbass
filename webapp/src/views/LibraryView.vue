<template>
  <div class="library-view">
    <!-- Search bar -->
    <div class="search-section">
      <div class="search-bar">
        <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск треков..."
          @input="debouncedSearch"
        />
        <button v-if="searchQuery" class="clear-search" @click="clearSearch">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Quick Access Grid -->
    <div class="quick-grid" v-if="!searchQuery">
      <!-- Liked tracks -->
      <div class="quick-item liked-quick" @click="$router.push('/liked')">
        <div class="quick-icon liked-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </div>
        <span class="quick-title">Любимое</span>
      </div>
      
      <!-- Albums -->
      <div class="quick-item" @click="$router.push('/albums')">
        <div class="quick-icon albums-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14.5c-2.49 0-4.5-2.01-4.5-4.5S9.51 7.5 12 7.5s4.5 2.01 4.5 4.5-2.01 4.5-4.5 4.5zm0-5.5c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
          </svg>
        </div>
        <span class="quick-title">Альбомы</span>
      </div>
      
      <!-- Artists -->
      <div class="quick-item" @click="$router.push('/artists')">
        <div class="quick-icon artists-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        </div>
        <span class="quick-title">Артисты</span>
      </div>
      
      <!-- Playlists -->
      <div class="quick-item" @click="$router.push('/playlists')">
        <div class="quick-icon playlists-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z"/>
          </svg>
        </div>
        <span class="quick-title">Плейлисты</span>
      </div>
    </div>

    <!-- Sort options -->
    <div class="sort-options">
      <select v-model="sortBy" @change="loadTracks">
        <option value="added_at">По дате</option>
        <option value="title">По названию</option>
        <option value="artist">По исполнителю</option>
        <option value="duration">По длительности</option>
      </select>
      <button class="sort-order" @click="toggleSortOrder">
        {{ sortOrder === 'desc' ? '↓' : '↑' }}
      </button>
    </div>

    <!-- Track list -->
    <div class="track-list" ref="trackListRef">
      <div v-if="loading && !tracks.length" class="loading">
        <div class="spinner"></div>
        <span>Загрузка...</span>
      </div>
      
      <template v-else>
        <TrackItem
          v-for="track in tracks"
          :key="track.id"
          :track="track"
          :isPlaying="playerStore.currentTrack?.id === track.id"
          :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === track.id"
          :isLiked="track.is_liked"
          @click="playTrack(track)"
          @like="handleLikeTrack(track)"
          @menu="openTrackMenu(track)"
        />
        
        <div v-if="hasMore" class="load-more">
          <button @click="loadMore" :disabled="loading">
            {{ loading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
        
        <div v-if="!tracks.length" class="empty-state">
          <span class="empty-icon">🎵</span>
          <h3>Библиотека пуста</h3>
          <p>Отправьте аудио боту, чтобы добавить треки</p>
        </div>
      </template>
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      :current-user-id="authStore.user?.id"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
      @addToPlaylist="handleAddToPlaylist"
      @edit="handleEditTrack"
      @download="handleDownloadTrack"
      @delete="handleDeleteTrack"
      @removeFromLibrary="handleRemoveFromLibrary"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import api, { playerApi } from '@/api/client'

const router = useRouter()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const sortBy = ref('added_at')
const sortOrder = ref('desc')
const loading = ref(false)
const tracks = ref([])
const page = ref(1)
const total = ref(0)
const perPage = 50

let searchTimeout = null

const hasMore = computed(() => tracks.value.length < total.value)

const loadTracks = async () => {
  loading.value = true
  try {
    await libraryStore.fetchTracks({
      page: page.value,
      per_page: perPage,
      search: searchQuery.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    
    tracks.value = libraryStore.tracks
    total.value = libraryStore.total
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  page.value++
  await loadTracks()
}

const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
    loadTracks()
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  page.value = 1
  loadTracks()
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  page.value = 1
  loadTracks()
}

// Like track
const handleLikeTrack = async (track) => {
  const newLikedState = await libraryStore.toggleLike(track.id)
  // Update local track state
  const idx = tracks.value.findIndex(t => t.id === track.id)
  if (idx !== -1) {
    tracks.value[idx].is_liked = newLikedState
  }
}

const playTrack = (track) => {
  playerStore.playTrack(track, tracks.value)
}

// Track menu state
const menuTrack = ref(null)
const showMenu = ref(false)

const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

// Menu handlers
const handleGoToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist)}`)
}

const handleGoToAlbum = (albumName, artist) => {
  // Find album by name and artist
  // For now, just close menu
  closeMenu()
}

const handleAddToPlaylist = (track) => {
  // TODO: Show playlist picker
  closeMenu()
}

const handleEditTrack = (track) => {
  // TODO: Show edit modal
  closeMenu()
}

const handleDownloadTrack = async (track) => {
  try {
    await playerApi.download(track.id)
  } catch (error) {
    console.error('Failed to download track:', error)
  }
  closeMenu()
}

const handleDeleteTrack = async (track) => {
  if (confirm('Удалить трек полностью?')) {
    await libraryStore.deleteTrack(track.id)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
  }
  closeMenu()
}

const handleRemoveFromLibrary = async (track) => {
  await libraryStore.removeFromLibrary(track.id)
  tracks.value = tracks.value.filter(t => t.id !== track.id)
  closeMenu()
}

onMounted(() => {
  loadTracks()
  libraryStore.fetchPlaylists()
  libraryStore.fetchArtists()
})
</script>

<style scoped>
.library-view {
  padding: 16px;
  padding-bottom: 120px; /* Space for player */
}

.search-section {
  margin-bottom: 16px;
}

.search-bar {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border-radius: 8px;
  padding: 8px 12px;
  gap: 8px;
}

.search-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 16px;
  outline: none;
}

.search-icon {
  color: var(--text-secondary);
}

.clear-search {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-elevated);
  border-radius: 6px;
  padding: 0;
  cursor: pointer;
  overflow: hidden;
  height: 56px;
  transition: background 0.2s;
}

.quick-item:active {
  background: var(--bg-highlight);
}

.quick-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.liked-icon {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: white;
}

.albums-icon {
  background: linear-gradient(135deg, #0891b2, #22d3ee);
  color: white;
}

.artists-icon {
  background: linear-gradient(135deg, #059669, #34d399);
  color: white;
}

.playlists-icon {
  background: linear-gradient(135deg, #d97706, #fbbf24);
  color: white;
}

.quick-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.sort-options {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.sort-options select {
  flex: 1;
  background: var(--bg-elevated);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 14px;
}

.sort-order {
  background: var(--bg-elevated);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.load-more button {
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  font-weight: 600;
  cursor: pointer;
}

.load-more button:disabled {
  opacity: 0.5;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
}
</style>
