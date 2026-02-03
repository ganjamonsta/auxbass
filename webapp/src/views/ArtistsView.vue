<template>
  <div class="artists-view">
    <!-- Scope switcher - unified neumorphic style -->
    <div v-if="!authStore.hasChannel" class="neu-tab-bar scope-switcher">
      <button 
        class="neu-tab" 
        :class="{ active: scope === 'library' }"
        @click="changeScope('library')"
      >
        <span class="neu-tab-content" data-text="Моя библиотека">Моя библиотека</span>
      </button>
      <button 
        class="neu-tab" 
        :class="{ active: scope === 'global' }"
        @click="changeScope('global')"
      >
        <span class="neu-tab-content" data-text="Общая">Общая</span>
      </button>
    </div>

    <!-- Search -->
    <SearchBar
      v-model="searchQuery"
      placeholder="Поиск исполнителей..."
      @input="debouncedSearch"
    />

    <!-- Sort options -->
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
    <div v-if="loading && !initialized" class="media-grid type-artist">
      <GridSkeleton v-for="i in 12" :key="i" type="artist" />
    </div>

    <!-- Artist grid with infinite scroll -->
    <template v-else>
      <MediaGrid
        type="artist"
        :items="artists"
        :loading="false"
        @click="goToArtist"
        @contextmenu="handleContextMenu"
      >
        <template #empty>
          <div class="empty-state">
            <span class="empty-icon"><User :size="48" /></span>
            <p v-if="searchQuery">Ничего не найдено</p>
            <p v-else>Нет исполнителей</p>
          </div>
        </template>
      </MediaGrid>

      <!-- Infinite scroll trigger -->
      <div ref="loadTriggerRef" class="load-trigger" v-show="hasMore && !loading"></div>
      
      <!-- Loading more with skeletons -->
      <div v-if="loadingMore" class="media-grid type-artist loading-more-grid">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useVirtualScroll, useSort, useDebouncedSearch } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import MediaGrid from '@/components/MediaGrid.vue'
import GridSkeleton from '@/components/GridSkeleton.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import { artistsApi } from '@/api/client'
import { User } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const handleContextMenu = ({ item, event }) => {
  openMenu('artist', item, 'library', event)
}

const router = useRouter()
const authStore = useAuthStore()

// Scope state
const SCOPE_KEY = 'artists-scope'
const scope = ref(localStorage.getItem(SCOPE_KEY) || 'library')

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('artists-sort', 'artists', { sortBy: 'name', sortOrder: 'asc' })

// Debounced search using composable
const { query: searchQuery, debouncedQuery: debouncedSearchQuery, search: debouncedSearch, clear: clearSearch } = useDebouncedSearch({
  onSearch: () => reset()
})

// Fetch function for virtual scroll
const fetchArtists = async ({ offset, limit }) => {
  const params = {
    offset,
    limit,
    sort_by: sortBy.value,
    sort_order: sortOrder.value
  }
  
  if (debouncedSearchQuery.value) {
    params.search = debouncedSearchQuery.value
  }
  
  // Use global or library endpoint based on scope
  const response = scope.value === 'global' 
    ? await artistsApi.getGlobal(params)
    : await artistsApi.getAll(params)
  
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
  reset,
  refresh
} = useVirtualScroll({
  fetchFn: fetchArtists,
  limit: 30,
  immediate: false, // We'll load after scope is set
  skeletonCount: 6
})

// Change scope handler
const changeScope = (newScope) => {
  // If trying to access library without channel, show prompt
  if (newScope === 'library' && !authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  scope.value = newScope
  localStorage.setItem(SCOPE_KEY, newScope)
  reset()
}

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
  const query = scope.value === 'global' ? { scope: 'global' } : {}
  router.push({ 
    path: `/artist/${encodeURIComponent(artist.name)}`,
    query
  })
}

// Обработчик сброса состояния
const handleResetState = (event) => {
  if (event.detail.route === '/artists') {
    // Сбрасываем поиск
    clearSearch()
    // Сбрасываем сортировку на дефолтную
    sortBy.value = 'name'
    sortOrder.value = 'asc'
    // Перезагружаем список
    reset()
  }
}

// Initial load
onMounted(() => {
  // If no channel and scope is library, switch to global
  if (!authStore.hasChannel && scope.value === 'library') {
    scope.value = 'global'
    localStorage.setItem(SCOPE_KEY, 'global')
  }
  
  // If channel is present (Premium), force global scope
  if (authStore.hasChannel) {
    scope.value = 'global'
  }

  // Initial load
  reset()
  
  // Слушаем событие сброса состояния
  window.addEventListener('reset-view-state', handleResetState)
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
})
</script>

<style scoped>
.artists-view {
  padding: 16px;
}

/* Scope switcher uses neu-tab-bar from design-system */
.scope-switcher {
  margin-bottom: 16px;
}

.scope-switcher .neu-tab {
  flex: 1;
}

/* sort-options, stats, empty-state, empty-icon, load-trigger, loading-more, spinner are in design-system.css */

/* Grid skeleton layout */
.media-grid.type-artist {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .media-grid.type-artist {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 16px;
  }
}
</style>
