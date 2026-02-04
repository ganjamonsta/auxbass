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
        {{ virtualGridRef?.total?.value ?? 0 }} исполнителей
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
      type="artist"
      :fetchFn="fetchArtists"
      :pageSize="30"
      :skeletonCount="12"
      @click="goToArtist"
      @contextmenu="handleContextMenu"
    >
      <template #empty>
        <span class="empty-icon"><User :size="48" /></span>
        <p v-if="searchQuery">Ничего не найдено</p>
        <p v-else>Нет исполнителей</p>
      </template>
    </VirtualGrid>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSort, useDebouncedSearch } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import VirtualGrid from '@/components/VirtualGrid.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import { artistsApi } from '@/api/client'
import { User } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const router = useRouter()
const authStore = useAuthStore()
const virtualGridRef = ref(null)

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
const { query: searchQuery, debouncedQuery: debouncedSearchQuery, search: debouncedSearch, clear: clearSearch } = useDebouncedSearch(
  () => virtualGridRef.value?.reset()
)

// Fetch function for virtual grid
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

// Change scope handler
const changeScope = (newScope) => {
  // If trying to access library without channel, show prompt
  if (newScope === 'library' && !authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  scope.value = newScope
  localStorage.setItem(SCOPE_KEY, newScope)
  virtualGridRef.value?.reset()
}

// Sort change handlers
const onNextSort = () => {
  nextSort()
  virtualGridRef.value?.reset()
}

const onToggleOrder = () => {
  toggleOrder()
  virtualGridRef.value?.reset()
}

// Navigation
const goToArtist = (artist) => {
  const query = scope.value === 'global' ? { scope: 'global' } : {}
  router.push({ 
    path: `/artist/${encodeURIComponent(artist.name)}`,
    query
  })
}

// Context menu
const handleContextMenu = ({ item, event }) => {
  openMenu('artist', item, 'library', event)
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
    virtualGridRef.value?.reset()
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

/* sort-options, stats, empty-state, empty-icon are in design-system.css */
</style>
