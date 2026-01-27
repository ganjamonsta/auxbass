<template>
  <div class="album-detail-view" v-if="album">
    <!-- Album header -->
    <div class="album-header">
      <div class="album-cover">
        <img v-if="album.cover_url" :src="album.cover_url" :alt="album.name" />
        <div v-else class="cover-placeholder">💿</div>
      </div>
      <div class="album-info">
        <h1>{{ album.name }}</h1>
        <p class="artist" @click="goToArtist">{{ album.artist_name }}</p>
        <p class="meta">
          <span v-if="album.release_date">{{ formatYear(album.release_date) }} • </span>
          {{ album.track_count }} треков
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="album-actions">
      <button class="play-all-btn" @click="playAll">
        <span>▶</span>
        Слушать
      </button>
      <button class="shuffle-btn" @click="shufflePlay">
        🔀
      </button>
    </div>

    <!-- Track list -->
    <div class="track-list">
      <TrackItem
        v-for="(track, index) in album.tracks"
        :key="track.id"
        :track="track"
        :trackNumber="index + 1"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="track.is_liked"
        :hideCover="true"
        @click="playTrack(track, index)"
        @like="handleLikeTrack(track)"
        @menu="openTrackMenu(track)"
      />
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @addToPlaylist="handleAddToPlaylist"
      @download="handleDownloadTrack"
    />
  </div>

  <div v-else-if="loading" class="loading">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import api from '@/api/client'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()

const album = ref(null)
const loading = ref(true)
const showMenu = ref(false)
const menuTrack = ref(null)

const loadAlbum = async () => {
  loading.value = true
  try {
    const response = await api.get(`/albums/${route.params.id}`)
    album.value = response.data
  } finally {
    loading.value = false
  }
}

const playAll = () => {
  if (album.value?.tracks?.length) {
    playerStore.playTrack(album.value.tracks[0], album.value.tracks)
  }
}

const shufflePlay = () => {
  if (album.value?.tracks?.length) {
    const shuffled = [...album.value.tracks].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled)
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, album.value.tracks, index)
}

const goToArtist = () => {
  router.push(`/artist/${encodeURIComponent(album.value.artist_name)}`)
}

// Track menu handlers
const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

const handleLikeTrack = async (track) => {
  try {
    if (track.is_liked) {
      await api.delete(`/tracks/${track.id}/like`)
      track.is_liked = false
    } else {
      await api.post(`/tracks/${track.id}/like`)
      track.is_liked = true
    }
  } catch (error) {
    console.error('Failed to toggle like:', error)
  }
}

const handleGoToArtist = () => {
  closeMenu()
  router.push(`/artist/${encodeURIComponent(menuTrack.value?.artist)}`)
}

const handleAddToPlaylist = () => {
  closeMenu()
  // TODO: implement playlist picker
}

const handleDownloadTrack = async () => {
  if (!menuTrack.value) return
  try {
    const response = await api.get(`/player/stream/${menuTrack.value.id}`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${menuTrack.value.artist} - ${menuTrack.value.title}.mp3`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download:', error)
  }
  closeMenu()
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
  loadAlbum()
})
</script>

<style scoped>
.album-detail-view {
  padding: 16px;
  padding-bottom: 120px;
}

.album-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.album-cover {
  width: 160px;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-elevated);
  flex-shrink: 0;
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
  font-size: 64px;
}

.album-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.album-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.artist {
  color: var(--text-secondary);
  margin: 0 0 4px 0;
  cursor: pointer;
}

.artist:hover {
  text-decoration: underline;
}

.meta {
  color: var(--text-tertiary);
  font-size: 13px;
  margin: 0;
}

.album-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
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

.track-list {
  display: flex;
  flex-direction: column;
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
