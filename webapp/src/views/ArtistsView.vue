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

    <!-- Pagination -->
    <div v-if="hasMore && !loading" class="load-more">
      <button @click="loadMore">Загрузить ещё</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/client'

const router = useRouter()

const artists = ref([])
const total = ref(0)
const loading = ref(false)
const searchQuery = ref('')
const offset = ref(0)
const limit = 30
const hasMore = ref(false)

let searchTimeout = null

const loadArtists = async (append = false) => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      offset: offset.value.toString(),
      limit: limit.toString()
    })
    if (searchQuery.value) {
      params.set('search', searchQuery.value)
    }
    
    const response = await api.get(`/artists?${params}`)
    
    if (append) {
      artists.value = [...artists.value, ...response.data.items]
    } else {
      artists.value = response.data.items
    }
    total.value = response.data.total
    hasMore.value = artists.value.length < total.value
  } finally {
    loading.value = false
  }
}

const debouncedSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    offset.value = 0
    loadArtists()
  }, 300)
}

const loadMore = () => {
  offset.value += limit
  loadArtists(true)
}

const goToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist.name)}`)
}

onMounted(() => {
  loadArtists()
})
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
