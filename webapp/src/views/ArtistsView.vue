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

    <!-- Stats -->
    <div class="stats">
      {{ total }} исполнителей
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
  fetchFn: async ({ offset, limit, search }) => {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString()
    })
    if (search) {
      params.set('search', search)
    }
    const response = await api.get(`/artists?${params}`)
    return response.data
  },
  limit: 30,
  mode: 'windowed'  // Memory optimized - only current page in memory
})

const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    setParams({ search: searchQuery.value || undefined })
  }, 300)
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
  margin-bottom: 20px;
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
