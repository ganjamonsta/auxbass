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

    <!-- Artist grid -->
    <div class="artist-grid" v-if="artists.length">
      <div
        v-for="artist in artists"
        :key="artist.name"
        class="artist-card"
        @click="goToArtist(artist)"
      >
        <div class="artist-image">
          <img v-if="artist.image_url" :src="artist.image_url" :alt="artist.name" />
          <div v-else class="image-placeholder">👤</div>
        </div>
        <div class="artist-name">{{ artist.name }}</div>
        <div class="artist-meta">
          {{ artist.track_count }} треков • {{ artist.album_count }} альбомов
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!loading" class="empty-state">
      <span class="empty-icon">👤</span>
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
import { useSort } from '@/composables'
import SortChips from '@/components/SortChips.vue'
import api from '@/api/client'

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

// Data state
const artists = ref([])
const total = ref(0)
const loading = ref(false)
const offset = ref(0)
const limit = 30

// Infinite scroll
const loadTrigger = ref(null)
let observer = null

const hasMore = ref(true)

// Load artists
const loadArtists = async (append = false) => {
  if (loading.value) return
  
  loading.value = true
  
  try {
    const params = new URLSearchParams({
      offset: append ? offset.value.toString() : '0',
      limit: limit.toString(),
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    })
    
    if (props.searchQuery) {
      params.set('search', props.searchQuery)
    }
    
    const response = await api.get(`/artists?${params}`)
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

// Setup infinite scroll with IntersectionObserver
onMounted(() => {
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
})
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

.artist-card {
  text-align: center;
  cursor: pointer;
}

.artist-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 8px;
}

.artist-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 40px;
}

.artist-name {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 2px;
}

.artist-meta {
  color: var(--text-tertiary);
  font-size: 11px;
  line-height: 1.3;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
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
</style>
