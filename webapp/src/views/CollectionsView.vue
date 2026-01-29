<template>
  <div class="collections-view">
    <!-- Section header with tab switcher -->
    <div class="section-header">
      <h1>Коллекции</h1>
      <div class="tab-switcher">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'albums' }"
          @click="setActiveTab('albums')"
        >
          💿 Альбомы
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'playlists' }"
          @click="setActiveTab('playlists')"
        >
          📁 Плейлисты
        </button>
      </div>
    </div>

    <!-- Albums Tab -->
    <div v-show="activeTab === 'albums'" class="tab-content">
      <!-- Scope switcher for albums -->
      <div class="scope-tabs">
        <button 
          class="scope-tab" 
          :class="{ active: albumScope === 'library' }"
          @click="changeAlbumScope('library')"
        >
          Моя библиотека
        </button>
        <button 
          class="scope-tab" 
          :class="{ active: albumScope === 'global' }"
          @click="changeAlbumScope('global')"
        >
          Общая
        </button>
      </div>

      <!-- Search -->
      <div class="search-bar">
        <input
          v-model="albumSearchQuery"
          type="text"
          placeholder="Поиск альбомов..."
          @input="debouncedAlbumSearch"
        />
      </div>

      <div class="view-header">
        <div class="header-left">
          <span class="count">{{ albumsTotal }} альбомов</span>
        </div>
        <SortChips
          :currentOption="albumSortOption"
          :sortOrder="albumSortOrder"
          @next="onNextAlbumSort"
          @toggle-order="onToggleAlbumOrder"
        />
      </div>

      <div class="albums-grid">
        <div
          v-for="album in albums"
          :key="album.id"
          class="album-card"
          @click="goToAlbum(album)"
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
            <div v-else class="cover-placeholder">💿</div>
            <button class="play-btn" @click.stop="playAlbum(album)">▶</button>
            <div v-if="album.total_tracks && album.track_count < album.total_tracks" class="progress-badge">
              {{ album.track_count }}/{{ album.total_tracks }}
            </div>
          </div>
          <div class="album-info">
            <span class="album-name">{{ album.name }}</span>
            <span class="album-artist">{{ album.artist }}</span>
          </div>
        </div>
      </div>

      <div v-if="loadingAlbums" class="loading">
        <div class="spinner"></div>
      </div>

      <PaginationNav
        v-if="albumsTotalPages > 1 && !loadingAlbums"
        :currentPage="albumsPage"
        :totalPages="albumsTotalPages"
        :pageInfo="albumsPageInfo"
        :isFirstPage="albumsPage === 1"
        :isLastPage="albumsPage >= albumsTotalPages"
        :loading="loadingAlbums"
        position="bottom"
        @goToPage="goToAlbumsPage"
        @goToFirst="() => goToAlbumsPage(1)"
        @goToLast="() => goToAlbumsPage(albumsTotalPages)"
        @prevPage="() => goToAlbumsPage(albumsPage - 1)"
        @nextPage="() => goToAlbumsPage(albumsPage + 1)"
      />
    </div>

    <!-- Playlists Tab -->
    <div v-show="activeTab === 'playlists'" class="tab-content">
      <!-- Search for playlists -->
      <div class="search-bar">
        <input
          v-model="playlistSearchQuery"
          type="text"
          placeholder="Поиск плейлистов..."
        />
      </div>

      <div class="view-header">
        <span class="count">{{ filteredPlaylists.length }} плейлистов</span>
        <button class="create-btn" @click="handleCreatePlaylist">
          ➕ Создать
        </button>
      </div>

      <div class="playlists-grid" v-if="filteredPlaylists.length">
        <div
          v-for="playlist in filteredPlaylists"
          :key="playlist.id"
          class="playlist-card"
          @click="$router.push(`/playlist/${playlist.id}`)"
        >
          <div class="playlist-cover">
            <img v-if="playlist.cover_url" :src="playlist.cover_url" />
            <div v-else class="cover-placeholder">🎵</div>
            <div v-if="playlist.is_public" class="public-badge">🌐</div>
          </div>
          <div class="playlist-name">{{ playlist.name }}</div>
          <div class="playlist-meta">{{ playlist.track_count }} треков</div>
        </div>
      </div>


      
      <div v-else-if="!loadingPlaylists && playlistSearchQuery && filteredPlaylists.length === 0" class="empty-state">
        <span class="empty-icon">🔍</span>
        <p>Ничего не найдено</p>
      </div>

      <div v-if="loadingPlaylists" class="loading">
        <div class="spinner"></div>
      </div>

      <!-- Public playlists section -->
      <div v-if="filteredPublicPlaylists.length && !playlistSearchQuery" class="public-section">
        <h3>🌐 Публичные плейлисты</h3>
        <div class="playlists-grid">
          <div
            v-for="playlist in publicPlaylists"
            :key="'public-' + playlist.id"
            class="playlist-card"
            @click="$router.push(`/playlist/${playlist.id}`)"
          >
            <div class="playlist-cover">
              <img v-if="playlist.cover_url" :src="playlist.cover_url" />
              <div v-else class="cover-placeholder">🎵</div>
            </div>
            <div class="playlist-name">{{ playlist.name }}</div>
            <div class="playlist-meta">
              {{ playlist.owner_name }} • {{ playlist.track_count }} треков
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create playlist modal -->
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
        <label class="checkbox-label">
          <input type="checkbox" v-model="newPlaylistPublic" />
          <span>Публичный плейлист</span>
        </label>
        <p class="hint-text">Публичные плейлисты видны в разделе «Коллекции»</p>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import PaginationNav from '@/components/PaginationNav.vue'
import SortChips from '@/components/SortChips.vue'
import api from '@/api/client'

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

// Tab state from uiStore
const activeTab = computed(() => uiStore.collectionsTab)

const setActiveTab = (tab) => {
  uiStore.setCollectionsTab(tab)
}

// Scope state for albums
const ALBUM_SCOPE_KEY = 'albums-scope'
const albumScope = ref(localStorage.getItem(ALBUM_SCOPE_KEY) || 'library')

const changeAlbumScope = (newScope) => {
  // If trying to access library without channel, show prompt
  if (newScope === 'library' && !authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  albumScope.value = newScope
  localStorage.setItem(ALBUM_SCOPE_KEY, newScope)
  albumsPage.value = 1
  loadAlbums()
}

// Sort options for albums
const ALBUM_SORT_OPTIONS = [
  { value: 'release_date', label: 'Дата', icon: '📅' },
  { value: 'name', label: 'Название', icon: '🔤' },
  { value: 'track_count', label: 'Треки', icon: '🎵' }
]

// Albums state
const albums = ref([])
const albumsTotal = ref(0)
const albumsPage = ref(1)
const albumsTotalPages = ref(1)
const loadingAlbums = ref(false)
const albumSortBy = ref('release_date')
const albumSortOrder = ref('desc')

// Album search state
const albumSearchQuery = ref('')
let albumSearchTimeout = null

// Debounced album search
const debouncedAlbumSearch = () => {
  if (albumSearchTimeout) {
    clearTimeout(albumSearchTimeout)
  }
  albumSearchTimeout = setTimeout(() => {
    albumsPage.value = 1
    loadAlbums()
  }, 300)
}
const albumSortOption = computed(() => {
  return ALBUM_SORT_OPTIONS.find(opt => opt.value === albumSortBy.value) || ALBUM_SORT_OPTIONS[0]
})
const ALBUMS_PER_PAGE = 30

// Computed page info for pagination
const albumsPageInfo = computed(() => {
  const itemsFrom = (albumsPage.value - 1) * ALBUMS_PER_PAGE + 1
  const itemsTo = Math.min(albumsPage.value * ALBUMS_PER_PAGE, albumsTotal.value)
  return {
    itemsFrom,
    itemsTo,
    itemsTotal: albumsTotal.value
  }
})

// Playlists state
const playlists = ref([])
const publicPlaylists = ref([])
const loadingPlaylists = ref(false)
const likedCount = ref(0)

// Playlist search state
const playlistSearchQuery = ref('')

// Filtered playlists computed - only public playlists
const filteredPlaylists = computed(() => {
  // Filter only public playlists first
  const publicOnly = playlists.value.filter(p => p.is_public)
  
  if (!playlistSearchQuery.value) {
    return publicOnly
  }
  const query = playlistSearchQuery.value.toLowerCase()
  return publicOnly.filter(p => 
    p.name.toLowerCase().includes(query)
  )
})

// Filtered public playlists computed
const filteredPublicPlaylists = computed(() => {
  if (!playlistSearchQuery.value) {
    return publicPlaylists.value
  }
  const query = playlistSearchQuery.value.toLowerCase()
  return publicPlaylists.value.filter(p => 
    p.name.toLowerCase().includes(query) ||
    (p.owner_name && p.owner_name.toLowerCase().includes(query))
  )
})

// Create modal
const showCreateModal = ref(false)
const newPlaylistName = ref('')
const newPlaylistPublic = ref(false)
const nameInput = ref(null)

// Handle create playlist - check for channel
const handleCreatePlaylist = () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  showCreateModal.value = true
}

// Albums functions
const loadAlbums = async () => {
  loadingAlbums.value = true
  try {
    const endpoint = albumScope.value === 'global' ? '/albums/global' : '/albums'
    const params = {
      offset: (albumsPage.value - 1) * ALBUMS_PER_PAGE,
      limit: ALBUMS_PER_PAGE,
      sort_by: albumSortBy.value,
      sort_order: albumSortOrder.value,
      min_tracks: albumScope.value === 'global' ? 1 : 2
    }
    
    if (albumSearchQuery.value) {
      params.search = albumSearchQuery.value
    }
    
    const response = await api.get(endpoint, { params })
    albums.value = response.data.items || []
    albumsTotal.value = response.data.total || 0
    albumsTotalPages.value = Math.ceil(albumsTotal.value / ALBUMS_PER_PAGE)
  } finally {
    loadingAlbums.value = false
  }
}

const goToAlbumsPage = (page) => {
  albumsPage.value = page
  loadAlbums()
}

const goToAlbum = (album) => {
  const query = albumScope.value === 'global' ? { scope: 'global' } : {}
  router.push({ 
    path: `/album/${album.id}`,
    query
  })
}

const onNextAlbumSort = () => {
  const idx = ALBUM_SORT_OPTIONS.findIndex(opt => opt.value === albumSortBy.value)
  const nextIdx = (idx + 1) % ALBUM_SORT_OPTIONS.length
  albumSortBy.value = ALBUM_SORT_OPTIONS[nextIdx].value
  albumsPage.value = 1
  loadAlbums()
}

const onToggleAlbumOrder = () => {
  albumSortOrder.value = albumSortOrder.value === 'asc' ? 'desc' : 'asc'
  albumsPage.value = 1
  loadAlbums()
}

const playAlbum = async (album) => {
  try {
    const params = albumScope.value === 'global' ? { scope: 'global' } : {}
    const response = await api.get(`/albums/${album.id}`, { params })
    const albumData = response.data
    
    // Get playable tracks - from full_tracklist or tracks array
    let tracks = []
    if (albumData.full_tracklist?.length) {
      tracks = albumData.full_tracklist
        .filter(item => item.track)
        .map(item => item.track)
    } else if (albumData.tracks?.length) {
      tracks = albumData.tracks
    }
    
    if (tracks.length) {
      playerStore.playTrack(tracks[0], tracks)
    }
  } catch (error) {
    console.error('Failed to load album:', error)
  }
}

// Playlists functions
const loadPlaylists = async () => {
  loadingPlaylists.value = true
  try {
    const response = await api.get('/playlists')
    playlists.value = response.data.items || response.data || []
  } finally {
    loadingPlaylists.value = false
  }
}

const loadPublicPlaylists = async () => {
  try {
    const response = await api.get('/playlists/public/explore', {
      params: { per_page: 10 }
    })
    // Filter out own playlists
    publicPlaylists.value = (response.data.items || []).filter(
      p => !playlists.value.some(own => own.id === p.id)
    )
  } catch (error) {
    console.error('Failed to load public playlists:', error)
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

const closeModal = () => {
  showCreateModal.value = false
  newPlaylistName.value = ''
  newPlaylistPublic.value = false
}

const createPlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  
  try {
    const response = await api.post('/playlists', {
      name: newPlaylistName.value.trim(),
      is_public: newPlaylistPublic.value
    })
    playlists.value.unshift(response.data)
    closeModal()
    router.push(`/playlist/${response.data.id}`)
  } catch (error) {
    console.error('Failed to create playlist:', error)
  }
}

// Load data on tab change
watch(activeTab, (tab) => {
  if (tab === 'albums' && albums.value.length === 0) {
    loadAlbums()
  } else if (tab === 'playlists' && playlists.value.length === 0) {
    loadPlaylists()
    loadPublicPlaylists()
    loadLikedCount()
  }
})

onMounted(() => {
  // If no channel and scope is library, switch to global
  if (!authStore.hasChannel && albumScope.value === 'library') {
    albumScope.value = 'global'
    localStorage.setItem(ALBUM_SCOPE_KEY, 'global')
  }
  
  // Load initial tab data
  if (activeTab.value === 'albums') {
    loadAlbums()
  } else {
    loadPlaylists()
    loadPublicPlaylists()
    loadLikedCount()
  }
})
</script>

<style scoped>
.collections-view {
  padding: 8px 16px 120px 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.section-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.tab-switcher {
  display: none;
  gap: 4px;
  background: var(--c-bg-0);
  border-radius: var(--r-md);
  padding: 4px;
  box-shadow:
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

/* Show tab-switcher only on desktop */
@media (min-width: 1024px) {
  .tab-switcher {
    display: flex;
  }
}

.tab-btn {
  padding: 8px 14px;
  background: transparent;
  border: none;
  border-radius: calc(var(--r-md) - 2px);
  color: var(--c-text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--c-text-1);
}

.tab-btn.active {
  background: var(--c-bg-2);
  color: var(--c-text-1);
  font-weight: 600;
  box-shadow:
    2px 2px 4px var(--sh-dark),
    -1px -1px 2px var(--sh-light);
}

.scope-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  margin-bottom: 16px;
  background: var(--c-bg-0);
  border-radius: var(--r-md);
  box-shadow:
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

.scope-tab {
  flex: 1;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: calc(var(--r-md) - 2px);
  color: var(--c-text-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.scope-tab:hover {
  color: var(--c-text-1);
}

.scope-tab.active {
  background: var(--accent);
  color: white;
  font-weight: 600;
  box-shadow:
    2px 2px 4px var(--sh-dark),
    0 0 10px var(--accent-glow);
}

/* Search bar - neumorphic inset style */
.search-bar {
  margin-bottom: 16px;
}

.search-bar input {
  width: 100%;
  padding: 14px 18px;
  background: var(--c-bg-0);
  border: none;
  border-radius: var(--r-lg);
  color: var(--c-text-1);
  font-size: 15px;
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light);
  outline: none;
  transition: box-shadow 0.2s ease;
}

.search-bar input:focus {
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light),
    0 0 0 2px var(--accent-glow);
}

.search-bar input::placeholder {
  color: var(--c-text-3);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.count {
  font-size: 14px;
  color: var(--text-secondary);
}

.create-btn {
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
}

/* Albums grid */
.albums-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (min-width: 400px) {
  .albums-grid {
    gap: 16px;
  }
}

@media (min-width: 500px) {
  .albums-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 700px) {
  .albums-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
}

@media (min-width: 900px) {
  .albums-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}

.album-card {
  cursor: pointer;
  transition: transform 0.2s;
  min-width: 0;
}

.album-card:active {
  transform: scale(0.98);
}

.album-cover {
  position: relative;
  aspect-ratio: 1;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 8px;
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
}

.play-btn {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s;
}

.album-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
}

.progress-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: var(--accent);
  font-size: 10px;
  font-weight: 600;
  padding: 3px 6px;
  border-radius: 10px;
}

.album-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.album-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-artist {
  font-size: 11px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Playlists */
.special-playlists {
  margin-bottom: 20px;
}

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

.playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.liked-card .playlist-cover {
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
}

.liked-cover {
  display: flex;
  align-items: center;
  justify-content: center;
}

.liked-icon {
  font-size: 40px;
}

.public-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
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

.public-section {
  margin-top: 32px;
}

.public-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 48px 24px;
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

/* Modal */
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
  padding: 20px;
}

.modal {
  background: var(--bg-elevated);
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}

.modal h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: var(--text-primary);
}

.modal input[type="text"] {
  width: 100%;
  padding: 14px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 16px;
  margin-bottom: 16px;
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
  margin-bottom: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.cancel-btn, .confirm-btn {
  flex: 1;
  padding: 12px;
  border-radius: 24px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.cancel-btn {
  background: var(--bg-highlight);
  color: var(--text-primary);
}

.confirm-btn {
  background: var(--accent);
  color: #000;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading */
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
