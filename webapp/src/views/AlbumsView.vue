<template>
  <div class="albums-view">
    <div class="view-header">
      <h1>Альбомы</h1>
      <span class="count">{{ total }} альбомов</span>
    </div>

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
        </div>
        <div class="album-info">
          <span class="album-name">{{ album.name }}</span>
          <span class="album-artist">{{ album.artist_name }}</span>
          <span class="track-count">{{ album.track_count }} треков</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <div v-if="hasMore && !loading" class="load-more">
      <button @click="loadMore">Загрузить ещё</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'

const playerStore = usePlayerStore()

const albums = ref([])
const loading = ref(false)
const offset = ref(0)
const total = ref(0)
const limit = 30

const hasMore = computed(() => albums.value.length < total.value)

const loadAlbums = async (append = false) => {
  loading.value = true
  try {
    const response = await api.get('/albums', {
      params: {
        offset: append ? offset.value : 0,
        limit: limit,
      }
    })
    
    if (append) {
      albums.value.push(...response.data.items)
    } else {
      albums.value = response.data.items
      offset.value = 0
    }
    total.value = response.data.total
    offset.value += response.data.items.length
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  await loadAlbums(true)
}

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

onMounted(() => {
  loadAlbums()
})
</script>

<style scoped>
.albums-view {
  padding: 16px;
  padding-bottom: 120px;
}

.view-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 24px;
}

.view-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.count {
  font-size: 14px;
  color: var(--text-secondary);
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

.loading, .load-more {
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

.load-more button {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  cursor: pointer;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
