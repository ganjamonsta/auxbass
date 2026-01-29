<template>
  <div class="library-albums">
    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ total }} альбомов
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

    <div class="albums-grid">
      <AlbumGridCard
        v-for="album in albums"
        :key="album.id"
        :album="album"
        @click="$router.push(`/album/${album.id}`)"
        @play="playAlbum"
      />
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>
    
    <div v-if="!loading && !albums.length" class="empty-state">
      <span class="empty-icon"><Disc3 :size="48" /></span>
      <h3 v-if="searchQuery">Ничего не найдено</h3>
      <p v-else>В библиотеке нет альбомов</p>
    </div>

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
import PaginationNav from '@/components/PaginationNav.vue'
import SortChips from '@/components/SortChips.vue'
import AlbumGridCard from '@/components/AlbumGridCard.vue'
import api from '@/api/client'
import { Disc3 } from 'lucide-vue-next'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const playerStore = usePlayerStore()

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('library-albums-sort', 'albums', { sortBy: 'release_date', sortOrder: 'desc' })

// Sort handlers
const onNextSort = () => {
  nextSort()
  goToFirst()
}

const onToggleOrder = () => {
  toggleOrder()
  goToFirst()
}

// Pagination with unified composable
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
    const params = { 
      offset, 
      limit,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    if (props.searchQuery) {
      params.search = props.searchQuery
    }
    const response = await api.get('/albums', { params })
    return response.data
  },
  limit: 30,
  mode: 'windowed'
})

// Watch search query to reload
watch(() => props.searchQuery, () => {
  goToFirst()
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
.library-albums {
  padding-bottom: 20px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}

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
  display: block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
