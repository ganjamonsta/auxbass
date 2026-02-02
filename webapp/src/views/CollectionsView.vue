<template>
  <div class="collections-view">
    <!-- Albums Tab -->
    <div v-show="activeTab === 'albums'" class="tab-content">
      <!-- Scope switcher for albums -->
      <div v-if="!authStore.hasChannel" class="neu-tab-bar scope-switcher">
        <button 
          class="neu-tab" 
          :class="{ active: albumScope === 'library' }"
          @click="changeAlbumScope('library')"
        >
          <span class="neu-tab-content" data-text="Моя библиотека">Моя библиотека</span>
        </button>
        <button 
          class="neu-tab" 
          :class="{ active: albumScope === 'global' }"
          @click="changeAlbumScope('global')"
        >
          <span class="neu-tab-content" data-text="Общая">Общая</span>
        </button>
      </div>

      <!-- Search -->
      <SearchBar
        v-model="albumSearchQuery"
        placeholder="Поиск альбомов..."
        @input="debouncedAlbumSearch"
      />

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

      <MediaGrid
        type="album"
        :items="albums"
        :loading="loadingAlbums"
        @click="goToAlbum"
        @play="playAlbum"
      />

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
      <SearchBar
        v-model="playlistSearchQuery"
        placeholder="Поиск плейлистов..."
      />

      <div class="view-header">
        <span class="count">{{ filteredPlaylists.length }} плейлистов</span>
        <button class="create-btn" @click="handleCreatePlaylist">
          <Plus :size="16" /> Создать
        </button>
      </div>

      <MediaGrid
        type="playlist"
        :items="filteredPlaylists"
        :loading="loadingPlaylists"
        @click="(p) => $router.push(`/playlist/${p.id}`)"
      >
        <template #empty>
           <div v-if="playlistSearchQuery" class="empty-results">
            <span class="empty-icon"><Search :size="48" /></span>
             <p>Ничего не найдено</p>
           </div>
           <p v-else>Нет плейлистов</p>
        </template>
      </MediaGrid>

      <!-- Public playlists section -->
      <div v-if="publicPlaylists.length && !playlistSearchQuery" class="public-section">
        <MediaGrid
          type="playlist"
          title="Публичные плейлисты"
          :items="publicPlaylists"
          @click="(p) => $router.push(`/playlist/${p.id}`)"
        />
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
import SearchBar from '@/components/ui/SearchBar.vue'
import MediaGrid from '@/components/MediaGrid.vue'
import api from '@/api/client'
import { Disc3, Folder, Plus, Music, Globe, Search, Play } from 'lucide-vue-next'

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
  { value: 'release_date', label: 'Дата', icon: 'Calendar' },
  { value: 'name', label: 'Название', icon: 'Type' },
  { value: 'track_count', label: 'Треки', icon: 'Music' }
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
  
  // If channel is present (Premium), force global scope as these sections are global-only for premium
  if (authStore.hasChannel) {
    albumScope.value = 'global' 
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
  padding: 8px 16px 180px 16px;
}

/* Scope switcher uses neu-tab-bar from design-system */
.scope-switcher {
  margin-bottom: 16px;
}

.scope-switcher .neu-tab {
  flex: 1;
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
  color: var(--c-text-2);
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
  width: auto !important;
  max-width: fit-content;
}

/* Playlists */
.special-playlists {
  margin-bottom: 20px;
}

.public-section {
  margin-top: 32px;
}

.public-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 16px;
}

/* Empty state */
.empty-results {
  text-align: center;
  padding: 48px 24px;
  color: var(--c-text-2);
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
  background: var(--c-bg-2);
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}

.modal h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: var(--c-text-1);
}

.modal input[type="text"] {
  width: 100%;
  padding: 14px 16px;
  background: var(--c-bg-1);
  border: 1px solid var(--c-bg-4);
  border-radius: 12px;
  color: var(--c-text-1);
  font-size: 16px;
  margin-bottom: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--c-text-2);
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
  background: var(--c-bg-3);
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
  color: var(--c-text-3);
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
  background: var(--c-bg-3);
  color: var(--c-text-1);
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
  border: 3px solid var(--c-bg-3);
  border-top-color: var(--c-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
