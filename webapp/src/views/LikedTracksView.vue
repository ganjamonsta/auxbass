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
      <div
        v-for="(track, index) in sortedTracks"
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
          <span class="track-artist">{{ track.artist }}</span>
        </div>
        <button class="like-btn liked" @click.stop="unlikeTrack(track)">
          ❤️
        </button>
      </div>
    </div>

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
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import api from '@/api/client'

const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()

const tracks = ref([])
const loading = ref(true)

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
    const response = await api.get('/library/liked')
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
    await api.delete(`/library/${track.id}/like`)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
    // Also update in library store if track exists there
    const storeTrack = libraryStore.tracks.find(t => t.id === track.id)
    if (storeTrack) storeTrack.is_liked = false
  } catch (error) {
    console.error('Failed to unlike track:', error)
  }
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

.track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.track-item:hover {
  background: var(--bg-highlight);
}

.track-item.playing {
  background: var(--bg-elevated);
}

.track-cover {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--bg-elevated);
}

.track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-cover .cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-title {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-item.playing .track-title {
  color: #ff4564;
}

.track-artist {
  color: var(--text-tertiary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.like-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
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
