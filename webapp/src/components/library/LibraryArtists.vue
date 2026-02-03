<template>
  <div class="library-artists">
    <!-- Sort options (Stats + SortChips) -->
    <div class="sort-options">
      <div class="stats">
        {{ total }} исполнителей
      </div>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Loading state with skeletons -->
    <div v-if="loading && !initialized" class="artist-grid">
      <GridSkeleton v-for="i in 12" :key="i" type="artist" />
    </div>

    <!-- Artist grid -->
    <template v-else>
      <div class="artist-grid" v-if="artists.length">
        <ArtistGridCard
          v-for="artist in artists"
          :key="artist.name"
          :artist="artist"
          @click="goToArtist"
          @contextmenu="(e) => openMenu('artist', artist, 'library', e)"
        />
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading" class="empty-state">
        <span class="empty-icon"><User :size="48" /></span>
        <p v-if="searchQuery">Ничего не найдено</p>
        <p v-else>Нет исполнителей</p>
      </div>

      <!-- Infinite scroll trigger -->
      <div ref="loadTriggerRef" class="load-trigger" v-show="hasMore && !loading"></div>

      <!-- Loading more with skeletons -->
      <div v-if="loadingMore" class="artist-grid loading-more-grid">
        <GridSkeleton 
          v-for="i in loadingSkeletonCount" 
          :key="'skeleton-more-' + i" 
          type="artist" 
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useVirtualScroll, useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import ArtistGridCard from '@/components/ArtistGridCard.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import api from '@/api/client'
import { User } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('library-artists-sort', 'artists', { sortBy: 'name', sortOrder: 'asc' })

// Fetch function for virtual scroll
const fetchArtists = async ({ offset, limit }) => {
  const params = {
    offset,
    limit,
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  
  if (props.searchQuery) {
    params.search = props.searchQuery
  }
  
  const response = await api.get('/artists', { params })
  return response.data
}

// Virtual scroll composable
const {
  items: artists,
  total,
  loading,
  loadingMore,
  hasMore,
  initialized,
  loadTriggerRef,
  loadingSkeletonCount,
  reset
} = useVirtualScroll({
  fetchFn: fetchArtists,
  limit: 30,
  skeletonCount: 6
})

// Watchers
watch(() => props.searchQuery, () => {
  reset()
})

// Sort change handlers
const onNextSort = () => {
  nextSort()
  reset()
}

const onToggleOrder = () => {
  toggleOrder()
  reset()
}

// Navigation
const goToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist.name)}`)
}
</script>

<style scoped>
.library-artists {
  padding-bottom: 20px;
}

.stats {
  color: var(--text-secondary);
  font-size: 14px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
}

.artist-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

@media (min-width: 400px) {
  .artist-grid {
    gap: 16px;
  }
}

@media (min-width: 500px) {
  .artist-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 700px) {
  .artist-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 20px;
  }
}

@media (min-width: 900px) {
  .artist-grid {
    grid-template-columns: repeat(6, 1fr);
  }
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-secondary);
}

/* empty-icon, load-trigger, loading-more, spinner are in design-system.css */
</style>
