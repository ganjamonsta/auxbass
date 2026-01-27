<template>
  <div class="artists-view">
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
      <div class="sort-controls">
        <select v-model="sortBy" @change="onSortChange">
          <option value="name">По имени</option>
          <option value="track_count">По трекам</option>
          <option value="album_count">По альбомам</option>
          <option value="latest_release">По дате релиза</option>
        </select>
        <button class="sort-order" @click="toggleSortOrder">
          {{ sortOrder === 'desc' ? '↓' : '↑' }}
        </button>
      </div>
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

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePagination } from '@/composables'
import PaginationNav from '@/components/PaginationNav.vue'
import api from '@/api/client'

const router = useRouter()

// Search state
const searchQuery = ref('')
let searchTimeout = null

// Sort state
const sortBy = ref('name')
const sortOrder = ref('asc')

// Pagination with unified composable (windowed mode for memory optimization)
const { 
  items: artists, 
  total, 
  loading,
  currentPage,
  totalPages,
  isFirstPage,
  isLastPage,
  pageInfo,
  setParams,
  goToPage,
  goToFirst,
  goToLast,
  prevPage,
  nextPage
} = usePagination({
  fetchFn: async ({ offset, limit, search, sort_by, sort_order }) => {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString(),
      sort_by: sort_by || 'name',
      sort_order: sort_order || 'asc'
    })
    if (search) {
      params.set('search', search)
    }
    const response = await api.get(`/artists?${params}`)
    return response.data
  },
  limit: 30,
  mode: 'windowed',  // Memory optimized - only current page in memory
  initialParams: {
    sort_by: 'name',
    sort_order: 'asc'
  }
})

const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    setParams({ search: searchQuery.value || undefined })
  }, 300)
}

const onSortChange = () => {
  // Set default order based on sort type
  if (sortBy.value === 'name') {
    sortOrder.value = 'asc'
  } else {
    sortOrder.value = 'desc'
  }
  setParams({ sort_by: sortBy.value, sort_order: sortOrder.value })
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  setParams({ sort_order: sortOrder.value })
}

const goToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist.name)}`)
}
</script>

<style scoped>
.artists-view {
  padding: 16px;
  padding-bottom: 120px;
}

.search-bar {
  margin-bottom: 16px;
}

.search-bar input {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 15px;
}

.search-bar input::placeholder {
  color: var(--text-tertiary);
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

.sort-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-controls select {
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

.sort-order {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-elevated);
  border: none;
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
}

.sort-order:hover {
  background: var(--bg-highlight);
}

.artist-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
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
  margin-bottom: 12px;
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
  font-size: 48px;
}

.artist-name {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.artist-meta {
  color: var(--text-tertiary);
  font-size: 12px;
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

.load-more {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.load-more button {
  padding: 12px 24px;
  background: var(--bg-elevated);
  border: none;
  border-radius: 20px;
  color: var(--text-primary);
  font-weight: 500;
  cursor: pointer;
}

.load-more button:hover {
  background: var(--bg-highlight);
}
</style>
