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

    <!-- Loading state with skeletons -->
    <div v-if="loading && !initialized" class="albums-grid">
      <GridSkeleton v-for="i in 12" :key="i" type="album" />
    </div>

    <!-- Albums grid -->
    <template v-else>
      <div class="albums-grid" v-if="albums.length">
        <AlbumGridCard
          v-for="album in albums"
          :key="album.id"
          :album="album"
          @click="$router.push(`/album/${album.id}`)"
          @play="playAlbum"
          @contextmenu="(e) => openMenu('album', album, 'library', e)"
        />
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading" class="empty-state">
        <span class="empty-icon"><Disc3 :size="48" /></span>
        <h3 v-if="searchQuery">Ничего не найдено</h3>
        <p v-else>В библиотеке нет альбомов</p>
      </div>

      <!-- Infinite scroll trigger -->
      <div ref="loadTriggerRef" class="load-trigger" v-show="hasMore && !loading"></div>

      <!-- Loading more with skeletons -->
      <div v-if="loadingMore" class="albums-grid loading-more-grid">
        <GridSkeleton 
          v-for="i in loadingSkeletonCount" 
          :key="'skeleton-more-' + i" 
          type="album" 
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { useVirtualScroll, useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import AlbumGridCard from '@/components/AlbumGridCard.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import api from '@/api/client'
import { Disc3 } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

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
  reset()
}

const onToggleOrder = () => {
  toggleOrder()
  reset()
}

// Infinite scroll with unified composable
const { 
  items: albums, 
  total, 
  loading,
  loadingMore,
  hasMore,
  initialized,
  loadTriggerRef,
  loadingSkeletonCount,
  reset,
  refresh
} = useVirtualScroll({
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
  skeletonCount: 6
})

// Watch search query to reload
watch(() => props.searchQuery, () => {
  reset()
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

/* spinner, empty-state, empty-icon, load-trigger, loading-more are in design-system.css */
</style>
