<template>
  <div class="albums-view">
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

    <!-- Top pagination (shows when not on first page) -->
    <PaginationNav
      v-if="!isFirstPage"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :pageInfo="pageInfo"
      :isFirstPage="isFirstPage"
      :isLastPage="isLastPage"
      :loading="loading"
      position="top"
      @goToFirst="goToFirst"
    />

    <MediaGrid
      type="album"
      :items="albums"
      :loading="loading"
      @click="(album) => $router.push(`/album/${album.id}`)"
      @play="playAlbum"
      @contextmenu="handleContextMenu"
    />

    <!-- Bottom pagination -->
    <PaginationNav
      v-if="totalPages > 1 && !loading"
      :currentPage="currentPage"
      :totalPages="totalPages"
      :pageInfo="pageInfo"
      :isFirstPage="isFirstPage"
      :isLastPage="isLastPage"
      :loading="loading"
      position="bottom"
      @goToPage="goToPage"
      @goToFirst="goToFirst"
      @goToLast="goToLast"
      @prevPage="prevPage"
      @nextPage="nextPage"
    />
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { usePagination, useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import PaginationNav from '@/components/PaginationNav.vue'
import SortChips from '@/components/SortChips.vue'
import MediaGrid from '@/components/MediaGrid.vue'
import api from '@/api/client'

// Universal context menu
const { openMenu } = useContextMenu()

const handleContextMenu = ({ item, event }) => {
  openMenu('album', item, 'library', event)
}

const playerStore = usePlayerStore()

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('albums-sort', 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

// Sort handlers
const onNextSort = () => {
  nextSort()
  goToFirst()
}

const onToggleOrder = () => {
  toggleOrder()
  goToFirst()
}

// Pagination with unified composable (windowed mode for memory optimization)
const { 
  items: albums, 
  total, 
  loading,
  currentPage,
  totalPages,
  isFirstPage,
  isLastPage,
  pageInfo,
  goToPage,
  goToFirst,
  goToLast,
  prevPage,
  nextPage,
  refresh
} = usePagination({
  fetchFn: async ({ offset, limit }) => {
    const response = await api.get('/albums', {
      params: { 
        offset, 
        limit,
        sort_by: sortBy.value,
        sort_order: sortOrder.value
      }
    })
    return response.data
  },
  limit: 30,
  mode: 'windowed'  // Memory optimized - only current page in memory
})

// Watch sort changes to refresh data
watch([sortBy, sortOrder], () => {
  refresh()
})

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
</script>
<style scoped>
.albums-view {
  padding: 16px;
  padding-bottom: 180px;
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
</style>
