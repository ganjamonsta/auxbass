<template>
  <div class="collections-view">
    <!-- Type Switcher (Tabs) - Desktop Only -->
    <div class="neu-tab-bar collections-tabs">
      <button 
        class="neu-tab"
        :class="{ active: activeTab === 'albums' }"
        @click="setActiveTab('albums')"
      >
        <span class="neu-tab-content" data-text="Альбомы">Альбомы</span>
      </button>
      <button 
        class="neu-tab"
        :class="{ active: activeTab === 'playlists' }"
        @click="setActiveTab('playlists')"
      >
        <span class="neu-tab-content" data-text="Плейлисты">Плейлисты</span>
      </button>
    </div>

    <!-- Albums Tab - using unified component -->
    <div v-show="activeTab === 'albums'" class="tab-content">
      <!-- Search -->
      <SearchBar
        v-model="albumSearchQuery"
        placeholder="Поиск альбомов..."
        @input="debouncedAlbumSearch"
      />

      <LibraryAlbums
        ref="albumsRef"
        scope="global"
        :searchQuery="debouncedAlbumQuery"
      />
    </div>

    <!-- Playlists Tab -->
    <div v-show="activeTab === 'playlists'" class="tab-content">
      <!-- Info banner -->
      <div class="info-banner">
        <div class="banner-icon">
          <Folder :size="20" />
        </div>
        <div class="banner-text">
          <div class="banner-title">Общие плейлисты</div>
          <div class="banner-description">Все плейлисты, доступные в системе</div>
        </div>
      </div>

      <!-- Search for playlists -->
      <SearchBar
        v-model="playlistSearchQuery"
        placeholder="Поиск плейлистов..."
      />

      <div class="view-header">
        <span class="count">{{ filteredPublicPlaylists.length }} плейлистов</span>
        <button class="create-btn" @click="showManageModal = true">
          <Plus :size="16" /> Добавить
        </button>
      </div>

      <MediaGrid
        type="playlist"
        :items="filteredPublicPlaylists"
        :loading="loadingPlaylists"
        @click="(p) => $router.push(`/playlist/${p.id}`)"
        @play="shufflePlaylist"
      >
        <template #empty>
           <div v-if="playlistSearchQuery" class="empty-results">
            <span class="empty-icon"><Search :size="48" /></span>
             <p>Ничего не найдено</p>
           </div>
           <p v-else>Нет публичных плейлистов</p>
        </template>
      </MediaGrid>
    </div>

    <!-- Manage playlists modal -->
    <div v-if="showManageModal" class="modal-overlay" @click.self="closeManageModal">
      <div class="modal manage-modal">
        <h2>Добавить в коллекции</h2>
        <p class="hint-text">Выберите плейлисты для отображения в общей коллекции</p>
        
        <div class="playlists-manage-list">
          <div 
            v-for="playlist in ownPlaylists" 
            :key="playlist.id"
            class="playlist-manage-item"
            @click="togglePlaylistStatus(playlist)"
          >
            <div class="playlist-manage-info">
              <div class="playlist-manage-cover">
                <img v-if="playlist.covers?.length" :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" />
                <div v-else class="playlist-manage-placeholder"><Music :size="20" /></div>
              </div>
              <div class="playlist-manage-text">
                <div class="playlist-manage-name">{{ playlist.name }}</div>
                <div class="playlist-manage-count">{{ playlist.track_count }} треков</div>
              </div>
            </div>
            <label class="checkbox-label compact">
              <input 
                type="checkbox" 
                :checked="playlist.is_public"
                @click.stop="togglePlaylistStatus(playlist)"
              />
            </label>
          </div>
        </div>
        
        <div class="modal-actions">
          <button class="cancel-btn" @click="closeManageModal">Закрыть</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useUIStore } from '@/stores/ui'
import { useDebouncedSearch } from '@/composables'
import SearchBar from '@/components/ui/SearchBar.vue'
import MediaGrid from '@/components/MediaGrid.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import api from '@/api/client'
import { Folder, Plus, Music, Search } from 'lucide-vue-next'
import { getCoverUrl, CoverSize } from '@/utils'

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const uiStore = useUIStore()

// Tab state from uiStore
const activeTab = computed(() => uiStore.collectionsTab)

const setActiveTab = (tab) => {
  uiStore.setCollectionsTab(tab)
}

// Refs to child components
const albumsRef = ref(null)

// Album search with debounce
const { 
  query: albumSearchQuery, 
  debouncedQuery: debouncedAlbumQuery, 
  search: debouncedAlbumSearch,
  clear: clearAlbumSearch 
} = useDebouncedSearch()

// Playlists state
const playlists = ref([])
const publicPlaylists = ref([])
const loadingPlaylists = ref(false)

// Playlist search state
const playlistSearchQuery = ref('')

// Filtered public playlists computed - combine own public + others public
const filteredPublicPlaylists = computed(() => {
  // Combine own public playlists and public playlists from others
  const ownPublic = playlists.value.filter(p => p.is_public)
  
  // Create a Set of own playlist IDs for efficient lookup
  const ownPlaylistIds = new Set(playlists.value.map(p => p.id))
  
  // Filter out any playlists that are already in user's playlists to avoid duplicates
  const othersPublic = publicPlaylists.value.filter(p => !ownPlaylistIds.has(p.id))
  
  const allPublic = [...ownPublic, ...othersPublic]
  
  if (!playlistSearchQuery.value) {
    return allPublic
  }
  const query = playlistSearchQuery.value.toLowerCase()
  return allPublic.filter(p => 
    p.name.toLowerCase().includes(query) ||
    (p.owner_name && p.owner_name.toLowerCase().includes(query))
  )
})

// Manage modal
const showManageModal = ref(false)

// Computed for own playlists only (for manage modal)
const ownPlaylists = computed(() => {
  // Filter only playlists owned by current user
  return playlists.value.filter(p => p.is_owner === true)
})

const closeManageModal = () => {
  showManageModal.value = false
}

const togglePlaylistStatus = async (playlist) => {
  try {
    const newStatus = !playlist.is_public
    await api.put(`/playlists/${playlist.id}`, {
      is_public: newStatus
    })
    playlist.is_public = newStatus
    
    // Update in library store
    const libraryPlaylist = libraryStore.playlists.find(p => p.id === playlist.id)
    if (libraryPlaylist) {
      libraryPlaylist.is_public = newStatus
    }
    
    uiStore.toast.success('Сохранено', `Плейлист ${newStatus ? 'добавлен в коллекции' : 'удален из коллекций'}`)
  } catch (error) {
    console.error('Failed to toggle playlist status:', error)
    uiStore.toast.error('Ошибка', 'Не удалось обновить статус')
  }
}

// Shuffle playlist using lazy loading - delegates to playerStore.playShuffleAll
const shufflePlaylist = async (playlist) => {
  try {
    await playerStore.playShuffleAll('playlist', playlist.id)
  } catch (error) {
    console.error('Failed to shuffle playlist:', error)
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

// Load data on tab change
watch(activeTab, (tab) => {
  if (tab === 'playlists' && playlists.value.length === 0) {
    loadPlaylists()
    loadPublicPlaylists()
  }
})

onMounted(() => {
  // Load initial tab data
  if (activeTab.value === 'playlists') {
    loadPlaylists()
    loadPublicPlaylists()
  }
  
  // Слушаем событие сброса состояния
  window.addEventListener('reset-view-state', handleResetState)
})

// Handle reset state event
const handleResetState = (event) => {
  if (event.detail.route === '/collections') {
    // Сбрасываем состояние до базового
    if (activeTab.value === 'albums') {
      // Сброс поиска
      clearAlbumSearch()
      // Сброс компонента альбомов
      albumsRef.value?.reset()
    } else if (activeTab.value === 'playlists') {
      // Сброс поиска плейлистов
      playlistSearchQuery.value = ''
    }
  }
}

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})
</script>

<style scoped>
.collections-view {
  padding: 8px 16px 16px 16px;
}

/* Tabs Styles - use design system */
.collections-tabs {
  margin-bottom: 20px;
  display: none; /* Hide on mobile, tabs are in PageHeader */
}

/* Show collections-tabs only on desktop */
@media (min-width: 1024px) {
  .collections-tabs {
    display: flex;
  }
}

/* Override base .neu-tab-bar for this specific use case */
.collections-tabs.neu-tab-bar {
  padding: 4px;
}

/* Info banner */
.info-banner {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 16px;
  background: var(--c-bg-2);
  border-radius: 12px;
  margin-bottom: 16px;
  border: 1px solid var(--c-bg-3);
}

.banner-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #000;
  border-radius: 10px;
}

.banner-text {
  flex: 1;
}

.banner-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 4px;
}

.banner-description {
  font-size: 13px;
  color: var(--c-text-2);
  line-height: 1.4;
}

/* Mobile adjustments */
@media (max-width: 1023px) {
  .info-banner {
    padding: 12px;
    gap: 10px;
  }

  .banner-title {
    font-size: 14px;
    margin-bottom: 2px;
  }

  .banner-description {
    font-size: 12px;
  }

  .banner-icon {
    width: 40px;
    height: 40px;
  }
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
  display: flex;
  align-items: center;
  gap: 4px;
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
  margin: 0 0 12px;
  font-size: 20px;
  color: var(--c-text-1);
}

/* Manage modal */
.manage-modal {
  max-width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.playlists-manage-list {
  flex: 1;
  overflow-y: auto;
  margin: 16px 0;
  max-height: 50vh;
}

.playlist-manage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--c-bg-3);
  border-radius: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.playlist-manage-item:hover {
  background: var(--c-bg-4);
}

.playlist-manage-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.playlist-manage-cover {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--c-bg-1);
  flex-shrink: 0;
}

.playlist-manage-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.playlist-manage-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-text-3);
}

.playlist-manage-text {
  flex: 1;
  min-width: 0;
}

.playlist-manage-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.playlist-manage-count {
  font-size: 13px;
  color: var(--c-text-3);
  margin-top: 2px;
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

.checkbox-label.compact {
  margin-bottom: 0;
  gap: 0;
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

.cancel-btn {
  flex: 1;
  padding: 12px;
  border-radius: 24px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  background: var(--c-bg-3);
  color: var(--c-text-1);
}
</style>
