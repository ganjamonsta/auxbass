<template>
  <div class="artists-view">
    <!-- Scope switcher - unified neumorphic style -->
    <div v-if="!authStore.hasChannel" class="neu-tab-bar scope-switcher">
      <button 
        class="neu-tab" 
        :class="{ active: scope === 'library' }"
        @click="changeScope('library')"
      >
        Моя библиотека
      </button>
      <button 
        class="neu-tab" 
        :class="{ active: scope === 'global' }"
        @click="changeScope('global')"
      >
        Общая
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

    <MediaGrid
      type="artist"
      :items="artists"
      :loading="loading"
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
    <div ref="loadTrigger" class="load-trigger" v-show="hasMore && !loading"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSort } from '@/composables'
import { useContextMenu } from '@/composables/useContextMenu'
import SortChips from '@/components/SortChips.vue'
import MediaGrid from '@/components/MediaGrid.vue'
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

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('artists-sort', 'artists', { sortBy: 'name', sortOrder: 'asc' })

// Data state
const artists = ref([])
const total = ref(0)
const loading = ref(false)
const offset = ref(0)
const limit = 30

// Search state
const searchQuery = ref('')
let searchTimeout = null

// Infinite scroll
const loadTrigger = ref(null)
let observer = null

const hasMore = ref(true)

// Load artists
const loadArtists = async (append = false) => {
  if (loading.value) return
  
  loading.value = true
  
  try {
    const params = {
      offset: append ? offset.value : 0,
      limit: limit,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    // Use global or library endpoint based on scope
    const response = scope.value === 'global' 
      ? await artistsApi.getGlobal(params)
      : await artistsApi.getAll(params)
    const data = response.data
    
    if (append) {
      artists.value.push(...data.items)
    } else {
      artists.value = data.items
      offset.value = 0
    }
    
    total.value = data.total
    offset.value += data.items.length
    hasMore.value = artists.value.length < total.value
    
  } catch (error) {
    console.error('Failed to load artists:', error)
  } finally {
    loading.value = false
  }
}

// Load more (for infinite scroll)
const loadMore = () => {
  if (hasMore.value && !loading.value) {
    loadArtists(true)
  }
}

// Reset and reload
const reset = () => {
  offset.value = 0
  hasMore.value = true
  loadArtists(false)
}

// Debounced search
const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    reset()
  }, 300)
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

// Setup infinite scroll with IntersectionObserver
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

  loadArtists()
  
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        loadMore()
      }
    },
    { rootMargin: '200px' }
  )
  
  if (loadTrigger.value) {
    observer.observe(loadTrigger.value)
  }
})

// Watch for trigger element changes
watch(loadTrigger, (el) => {
  if (el && observer) {
    observer.observe(el)
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<style scoped>
.artists-view {
  padding: 16px;
  padding-bottom: 120px;
}

/* Scope switcher uses neu-tab-bar from design-system */
.scope-switcher {
  margin-bottom: 16px;
}

.scope-switcher .neu-tab {
  flex: 1;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 12px;
}

.stats {
  color: var(--c-text-2);
  font-size: 14px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  color: var(--c-text-2);
}

.empty-icon {
  display: block;
  margin-bottom: 16px;
  color: var(--c-text-3);
}

.load-trigger {
  height: 1px;
}
</style>
