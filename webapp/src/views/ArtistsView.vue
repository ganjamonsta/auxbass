<template>
  <div class="artists-view">
    <!-- Scope tabs -->
    <div class="scope-tabs">
      <button 
        class="scope-tab" 
        :class="{ active: scope === 'library' }"
        @click="changeScope('library')"
      >
        Моя библиотека
      </button>
      <button 
        class="scope-tab" 
        :class="{ active: scope === 'global' }"
        @click="changeScope('global')"
      >
        Общая
      </button>
    </div>

    <!-- Search -->
    <div class="search-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Поиск исполнителей..."
        @input="debouncedSearch"
      />
    </div>

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

    <!-- Artist grid -->
    <div class="artist-grid" v-if="artists.length">
      <ArtistGridCard
        v-for="artist in artists"
        :key="artist.name"
        :artist="artist"
        @click="goToArtist"
      />
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="empty-state">
      <span class="empty-icon"><User :size="48" /></span>
      <p v-if="searchQuery">Ничего не найдено</p>
      <p v-else>Нет исполнителей</p>
    </div>

    <!-- Loading indicator -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Infinite scroll trigger -->
    <div ref="loadTrigger" class="load-trigger" v-show="hasMore && !loading"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSort } from '@/composables'
import SortChips from '@/components/SortChips.vue'
import ArtistGridCard from '@/components/ArtistGridCard.vue'
import { artistsApi } from '@/api/client'
import { User } from 'lucide-vue-next'

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

.scope-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  margin-bottom: 16px;
  background: var(--c-bg-0);
  border-radius: var(--r-md);
  box-shadow:
    inset 2px 2px 4px var(--sh-inset-dark),
    inset -1px -1px 3px var(--sh-inset-light);
}

.scope-tab {
  flex: 1;
  padding: 10px 14px;
  background: transparent;
  border: none;
  border-radius: calc(var(--r-md) - 2px);
  color: var(--c-text-2);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.scope-tab:hover {
  color: var(--c-text-1);
}

.scope-tab.active {
  background: var(--accent);
  color: var(--accent-text, #000);
  font-weight: 600;
  box-shadow:
    2px 2px 4px var(--sh-dark),
    0 0 10px var(--accent-glow);
}

/* Search bar - neumorphic inset style */
.search-bar {
  margin-bottom: 16px;
}

.search-bar input {
  width: 100%;
  padding: 14px 18px;
  background: var(--c-bg-0);
  border: none;
  border-radius: var(--r-lg);
  color: var(--c-text-1);
  font-size: 15px;
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light);
  outline: none;
  transition: box-shadow 0.2s ease;
}

.search-bar input:focus {
  box-shadow:
    inset 3px 3px 6px var(--sh-inset-dark),
    inset -2px -2px 4px var(--sh-inset-light),
    0 0 0 2px var(--accent-glow);
}

.search-bar input::placeholder {
  color: var(--c-text-3);
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

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-trigger {
  height: 1px;
}
</style>
