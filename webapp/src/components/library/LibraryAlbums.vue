<template>
  <div class="library-albums">
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

    <div class="albums-grid">
      <div
        v-for="album in albums"
        :key="album.id"
        class="album-card"
        @click="$router.push(`/album/${album.id}`)"
      >
        <div class="album-cover">
          <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
          <div v-else class="cover-placeholder">💿</div>
          <button class="play-btn" @click.stop="playAlbum(album)">▶</button>
          <!-- Progress indicator if we have total_tracks -->
          <div v-if="album.total_tracks && album.track_count < album.total_tracks" class="progress-badge">
            {{ album.track_count }}/{{ album.total_tracks }}
          </div>
        </div>
        <div class="album-info">
          <span class="album-name">{{ album.name }}</span>
          <span class="album-artist">{{ album.artist }}</span>
          <span class="track-count">
            <template v-if="album.total_tracks">
              {{ album.track_count }}/{{ album.total_tracks }} треков
            </template>
            <template v-else>
              {{ album.track_count }} треков
            </template>
          </span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>
    
    <div v-if="!loading && !albums.length" class="empty-state">
      <span class="empty-icon">💿</span>
      <h3 v-if="searchQuery">Ничего не найдено</h3>
      <p v-else>В библиотеке нет альбомов</p>
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
import { watch } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { usePagination } from '@/composables'
import PaginationNav from '@/components/PaginationNav.vue'
import api from '@/api/client'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const playerStore = usePlayerStore()

// Pagination with unified composable
const { 
  items: albums, 
  total, 
  loading,
  currentPage,
  totalPages,
  isFirstPage,
  isLastPage,
  pageInfo,
  goToPage,
  goToFirst,
  goToLast,
  prevPage,
  nextPage,
  refresh // Assuming refresh or reload exists, or I can just re-trigger fetch
} = usePagination({
  fetchFn: async ({ offset, limit }) => {
    // Pass search query if API supports it, currently backend might not.
    // If backend ignores extra params, this is safe.
    const params = { offset, limit }
    if (props.searchQuery) {
      params.search = props.searchQuery
    }
    const response = await api.get('/albums', { params })
    return response.data
  },
  limit: 30,
  mode: 'windowed'
})

// Watch search query to reload
watch(() => props.searchQuery, () => {
    goToFirst()
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

.albums-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.album-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.album-card:active {
  transform: scale(0.98);
}

.album-cover {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  margin-bottom: 8px;
}

.album-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 48px;
}

.play-btn {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent);
  border: none;
  color: #000;
  font-size: 16px;
  cursor: pointer;
  opacity: 0;
  transform: translateY(8px);
  transition: all 0.2s;
}

.album-card:hover .play-btn {
  opacity: 1;
  transform: translateY(0);
}

.progress-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
}

.album-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.album-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-artist {
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-count {
  font-size: 12px;
  color: var(--text-tertiary);
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

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
