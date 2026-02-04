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
        <span class="count">{{ virtualGridRef?.total?.value ?? 0 }} альбомов</span>
      </div>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Spotify-style virtual grid -->
    <VirtualGrid
      ref="virtualGridRef"
      type="album"
      :fetchFn="fetchAlbums"
      :pageSize="30"
      :skeletonCount="12"
      @click="goToAlbum"
      @play="playAlbum"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <span class="empty-icon"><Disc3 :size="48" /></span>
        <h3 v-if="searchQuery">Ничего не найдено</h3>
        <p v-else>Нет альбомов</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useSort, useDebouncedSearch } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import api from '@/api/client'
import { Disc3 } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const router = useRouter()
const playerStore = usePlayerStore()
const virtualGridRef = ref(null)

// Debounced search using composable
const { query: searchQuery, debouncedQuery: debouncedSearchQuery, search: debouncedSearch } = useDebouncedSearch({
  onSearch: () => virtualGridRef.value?.reset()
})

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('albums-sort', 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

// Fetch function for virtual grid
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

// Sort handlers
const onNextSort = () => {
  nextSort()
  virtualGridRef.value?.reset()
}

const onToggleOrder = () => {
  toggleOrder()
  virtualGridRef.value?.reset()
}

// Navigation
const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

// Play album
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

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('album', item, 'library', event)
}
</script>

<style scoped>
.albums-view {
  padding: 16px;
}

/* view-header, header-left, count are in design-system.css */
</style>
