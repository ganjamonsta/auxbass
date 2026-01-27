<template>
  <div class="liked-tracks-view">
    <!-- Header -->
    <div class="liked-header">
      <div class="liked-cover">
        <span class="liked-icon">❤️</span>
      </div>
      <div class="liked-info">
        <h1>Понравившиеся</h1>
        <p class="meta">{{ tracks.length }} треков</p>
      </div>
    </div>

    <!-- Actions -->
    <div class="liked-actions">
      <button class="play-all-btn" @click="playAll" :disabled="!tracks.length">
        <span>▶</span>
        Слушать
      </button>
      <button class="shuffle-btn" @click="shufflePlay" :disabled="!tracks.length">
        🔀
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Track list -->
    <div class="track-list" v-else-if="tracks.length">
      <TrackItem
        v-for="(track, index) in sortedTracks"
        :key="track.id"
        :track="track"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="true"
        @click="playTrack(track, index)"
        @like="unlikeTrack(track)"
        @menu="openTrackMenu(track)"
      />
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
      @addToPlaylist="handleAddToPlaylist"
      @download="handleDownloadTrack"
    />

    <!-- Empty state -->
    <div v-else class="empty-state">
      <span class="empty-icon">❤️</span>
      <p>Нет понравившихся треков</p>
      <p class="hint">Нажмите ♡ на треке, чтобы добавить</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import api from '@/api/client'

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()

const tracks = ref([])
const loading = ref(true)
const showMenu = ref(false)
const menuTrack = ref(null)

const sortedTracks = computed(() => {
  return [...tracks.value].sort((a, b) => {
    const dateA = new Date(a.liked_at || 0)
    const dateB = new Date(b.liked_at || 0)
    return dateB - dateA
  })
})

const loadLikedTracks = async () => {
  loading.value = true
  try {
    const response = await api.get('/tracks/liked')
    tracks.value = response.data.items || response.data || []
  } catch (error) {
    console.error('Failed to load liked tracks:', error)
  } finally {
    loading.value = false
  }
}

const playTrack = (track, index) => {
  playerStore.playTrack(track, sortedTracks.value, index)
}

const playAll = () => {
  if (sortedTracks.value.length > 0) {
    playerStore.playTrack(sortedTracks.value[0], sortedTracks.value, 0)
  }
}

const shufflePlay = () => {
  if (sortedTracks.value.length > 0) {
    const shuffled = [...sortedTracks.value].sort(() => Math.random() - 0.5)
    playerStore.playTrack(shuffled[0], shuffled, 0)
  }
}

const unlikeTrack = async (track) => {
  try {
    await api.delete(`/tracks/${track.id}/like`)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
    // Also update in library store if track exists there
    const storeTrack = libraryStore.tracks.find(t => t.id === track.id)
    if (storeTrack) storeTrack.is_liked = false
  } catch (error) {
    console.error('Failed to unlike track:', error)
  }
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

const handleGoToArtist = () => {
  closeMenu()
  router.push(`/artist/${encodeURIComponent(menuTrack.value?.artist)}`)
}

const handleGoToAlbum = () => {
  closeMenu()
  const albumId = menuTrack.value?.album?.id || menuTrack.value?.album_id
  if (albumId) {
    router.push(`/album/${albumId}`)
  }
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

onMounted(() => {
  loadLikedTracks()
})
</script>

<style scoped>
.liked-tracks-view {
  padding: 16px;
  padding-bottom: 140px;
}

.liked-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.liked-cover {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ff4564, #c8325a);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.liked-icon {
  font-size: 48px;
}

.liked-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.liked-info h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.liked-info .meta {
  color: var(--text-tertiary);
  font-size: 14px;
  margin: 0;
}

.liked-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.play-all-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #ff4564, #c8325a);
  color: white;
  border: none;
  border-radius: 24px;
  padding: 12px 32px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
}

.play-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.shuffle-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--bg-elevated);
  border: none;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.shuffle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  border-top-color: #ff4564;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--text-secondary);
}

.empty-state .empty-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state p {
  margin: 0 0 8px 0;
}

.empty-state .hint {
  font-size: 13px;
  color: var(--text-tertiary);
}
</style>
