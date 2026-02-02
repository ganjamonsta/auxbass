<template>
  <div class="albums-view">
    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск альбомов..."
      @input="debouncedSearch"
    />

    <div class="view-header">
      <div class="header-left">
        <h1>Альбомы</h1>
        <span class="count">{{ total }} альбомов</span>
      </div>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Loading state with skeletons -->
    <div v-if="loading && !initialized" class="media-grid type-album">
      <GridSkeleton v-for="i in 12" :key="i" type="album" />
    </div>

    <!-- Album grid with infinite scroll -->
    <template v-else>
      <MediaGrid
        type="album"
        :items="albums"
        :loading="false"
        @click="(album) => $router.push(`/album/${album.id}`)"
        @play="playAlbum"
        @contextmenu="handleContextMenu"
      />

      <!-- Infinite scroll trigger -->
      <div ref="loadTriggerRef" class="load-trigger" v-show="hasMore && !loading"></div>
      
      <!-- Loading more indicator -->
      <div v-if="loadingMore" class="loading-more">
        <div class="spinner"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useVirtualScroll, useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import MediaGrid from '@/components/MediaGrid.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import api from '@/api/client'

// Universal context menu
const { openMenu } = useContextMenu()

const handleContextMenu = ({ item, event }) => {
  openMenu('album', item, 'library', event)
}

const playerStore = usePlayerStore()

// Search state
const searchQuery = ref('')
const debouncedSearchQuery = ref('')
let searchTimeout = null

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('albums-sort', 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

// Fetch function for virtual scroll
const fetchAlbums = async ({ offset, limit }) => {
  const response = await api.get('/albums', {
    params: { 
      offset, 
      limit,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
      search: debouncedSearchQuery.value || undefined
    }
  })
  return response.data
}

// Virtual scroll composable
const {
  items: albums,
  total,
  loading,
  loadingMore,
  hasMore,
  initialized,
  loadTriggerRef,
  reset,
  refresh
} = useVirtualScroll({
  fetchFn: fetchAlbums,
  limit: 30
})

// Debounced search
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedSearchQuery.value = searchQuery.value
    reset()
  }, 300)
}

// Sort handlers
const onNextSort = () => {
  nextSort()
  reset()
}

const onToggleOrder = () => {
  toggleOrder()
  reset()
}

const playAlbum = async (album) => {
  try {
    const response = await api.get(`/albums/${album.id}`)
    if (response.data.tracks?.length) {
      playerStore.playTrack(response.data.tracks[0], response.data.tracks)
    }
  } catch (error) {
    console.error('Failed to load album:', error)
  }
}

onUnmounted(() => {
  if (searchTimeout) clearTimeout(searchTimeout)
})
</script>
<style scoped>
.albums-view {
  padding: 16px;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.view-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.count {
  font-size: 14px;
  color: var(--text-secondary);
}

.load-trigger {
  height: 1px;
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--bg-highlight, rgba(255,255,255,0.1));
  border-top-color: var(--accent, #1DB954);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Grid skeleton layout */
.media-grid.type-album {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .media-grid.type-album {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
  }
}
</style>
