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

    <!-- Quick stats -->
    <div class="quick-stats" v-if="!searchQuery">
      <div class="stat-card" @click="$router.push('/albums')">
        <span class="stat-icon">💿</span>
        <span class="stat-value">{{ stats?.album_count || 0 }}</span>
        <span class="stat-label">Альбомов</span>
      </div>
      <div class="stat-card" @click="$router.push('/artists')">
        <span class="stat-icon">🎤</span>
        <span class="stat-value">{{ libraryStore.artists?.length || 0 }}</span>
        <span class="stat-label">Исполнителей</span>
      </div>
      <div class="stat-card" @click="$router.push('/playlists')">
        <span class="stat-icon">📁</span>
        <span class="stat-value">{{ libraryStore.playlists?.length || 0 }}</span>
        <span class="stat-label">Плейлистов</span>
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
import api from '@/api/client'

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
const stats = ref(null)

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
  // TODO: Download track
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

const loadStats = async () => {
  try {
    const response = await api.get('/library/stats')
    stats.value = response.data
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

onMounted(() => {
  loadTracks()
  loadStats()
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

.quick-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-elevated);
  border-radius: 12px;
  padding: 16px 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.stat-card:active {
  background: var(--bg-highlight);
}

.stat-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
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
