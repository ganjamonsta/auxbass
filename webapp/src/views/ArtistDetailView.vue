<template>
  <div class="artist-detail-view" v-if="artist">
    <!-- Artist header -->
    <div class="artist-header">
      <div class="artist-image">
        <img v-if="artist.image_url" :src="artist.image_url" :alt="artist.name" />
        <div v-else class="image-placeholder">👤</div>
      </div>
      <div class="artist-info">
        <h1>{{ artist.name }}</h1>
        <p class="meta">
          {{ artist.track_count }} треков • {{ artist.album_count }} альбомов
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="artist-actions">
      <button class="play-all-btn" @click="playAll">
        <span>▶</span>
        Слушать всё
      </button>
      <button class="shuffle-btn" @click="shufflePlay">
        🔀
      </button>
    </div>

    <!-- Albums section -->
    <section v-if="artist.albums?.length" class="section">
      <h2>Альбомы</h2>
      <div class="albums-row">
        <div
          v-for="album in artist.albums"
          :key="album.id"
          class="album-card"
          @click="goToAlbum(album)"
        >
          <div class="album-cover">
            <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
            <div v-else class="cover-placeholder">💿</div>
          </div>
          <div class="album-name">{{ album.name }}</div>
          <div class="album-year" v-if="album.release_date">
            {{ formatYear(album.release_date) }}
          </div>
        </div>
      </div>
    </section>

    <!-- Tracks section -->
    <section class="section">
      <h2>Все треки</h2>
      <div class="track-list">
        <div
          v-for="(track, index) in artist.tracks"
          :key="track.id"
          class="track-item"
          :class="{ playing: playerStore.currentTrack?.id === track.id }"
          @click="playTrack(track, index)"
        >
          <div class="track-cover">
            <img v-if="track.cover_url" :src="track.cover_url" :alt="track.title" />
            <div v-else class="cover-placeholder">🎵</div>
          </div>
          <div class="track-info">
            <span class="track-title">{{ track.title }}</span>
            <span class="track-album" v-if="track.album">{{ track.album }}</span>
          </div>
          <span class="track-duration">{{ formatDuration(track.duration) }}</span>
        </div>
      </div>
    </section>
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()

const artist = ref(null)
const loading = ref(true)

const loadArtist = async () => {
  loading.value = true
  try {
    const name = decodeURIComponent(route.params.name)
    const response = await api.get(`/artists/${encodeURIComponent(name)}`)
    artist.value = response.data
  } finally {
    loading.value = false
  }
}

const playAll = () => {
  if (artist.value?.tracks?.length) {
    playerStore.playTrack(artist.value.tracks[0], artist.value.tracks)
  }
}

const shufflePlay = () => {
  if (artist.value?.tracks?.length) {
    const shuffled = [...artist.value.tracks].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, artist.value.tracks, index)
}

const goToAlbum = (album) => {
  router.push(`/album/${album.id}`)
}

const formatDuration = (seconds) => {
  if (!seconds) return '--:--'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatYear = (date) => {
  if (!date) return ''
  return new Date(date).getFullYear()
}

onMounted(() => {
  loadArtist()
})
</script>

<style scoped>
.artist-detail-view {
  padding: 16px;
  padding-bottom: 120px;
}

.artist-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.artist-image {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.artist-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.artist-image .image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 56px;
}

.artist-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.artist-info h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.meta {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0;
}

.artist-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}

.play-all-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 12px 32px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.shuffle-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  font-size: 18px;
  cursor: pointer;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
}

.albums-row {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
  -webkit-overflow-scrolling: touch;
}

.albums-row::-webkit-scrollbar {
  height: 4px;
}

.albums-row::-webkit-scrollbar-thumb {
  background: var(--bg-highlight);
  border-radius: 2px;
}

.album-card {
  flex-shrink: 0;
  width: 140px;
  cursor: pointer;
}

.album-cover {
  width: 140px;
  height: 140px;
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
  font-size: 40px;
}

.album-name {
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.album-year {
  color: var(--text-tertiary);
  font-size: 12px;
}

.track-list {
  display: flex;
  flex-direction: column;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.track-item:hover {
  background: var(--bg-elevated);
}

.track-item.playing {
  background: var(--bg-highlight);
}

.track-item.playing .track-title {
  color: var(--accent);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-cover .cover-placeholder {
  font-size: 20px;
}

.track-info {
  flex: 1;
  min-width: 0;
}

.track-title {
  display: block;
  color: var(--text-primary);
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-album {
  display: block;
  color: var(--text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-duration {
  color: var(--text-tertiary);
  font-size: 13px;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px;
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
</style>
