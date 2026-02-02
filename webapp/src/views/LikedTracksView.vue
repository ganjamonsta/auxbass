<template>
  <div class="liked-tracks-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </div>
      <h2>Понравившиеся</h2>
      <p>Подключите Telegram-канал, чтобы сохранять понравившиеся треки</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="liked-header">
      <div class="liked-cover">
        <svg class="liked-icon" width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </div>
      <div class="liked-info">
        <h1>Понравившиеся</h1>
        <p class="meta">{{ tracks.length }} треков</p>
      </div>
    </div>

    <!-- Actions -->
    <div class="liked-actions">
      <div class="action-buttons" v-if="tracks.length">
        <button class="action-btn play-btn" @click="playAll">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
          </svg>
        </button>
      </div>
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
        @menu="(e) => openMenu('track', track, 'liked', e)"
        @download="handleDirectDownload(track)"
        @hdNotice="handleHdNotice"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
        </svg>
      </div>
      <p>Нет понравившихся треков</p>
      <p class="hint">Нажмите ♡ на треке, чтобы добавить</p>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useContextMenu } from '@/composables/useContextMenu'
import TrackItem from '@/components/TrackItem.vue'
import api, { playerApi } from '@/api/client'

// Universal context menu
const { openMenu } = useContextMenu()

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

const goToChannelSetup = () => {
  router.push('/settings#channel')
}

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
    await libraryStore.toggleLike(track.id)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
  } catch (error) {
    console.error('Failed to unlike track:', error)
  }
}

// Handle direct download from TrackItem (for large/HD files)
const handleDirectDownload = async (track) => {
  try {
    await playerApi.download(track.id)
    uiStore.toast.success('Трек отправлен', 'Проверьте сообщения в Telegram')
  } catch (error) {
    console.error('Failed to download track:', error)
    const errorMsg = error.response?.data?.detail || 'Ошибка отправки'
    uiStore.toast.error('Не удалось отправить', errorMsg)
  }
}

// HD track notice - show that track is only available for download
const handleHdNotice = (track) => {
  const sizeMB = track.file_size ? (track.file_size / 1024 / 1024).toFixed(1) : '20+'
  uiStore.toast.info('Только HD', `Этот трек (${sizeMB} MB) доступен только для скачивания. Используйте кнопку загрузки.`)
}

onMounted(() => {
  loadLikedTracks()
})
</script>

<style scoped>
.liked-tracks-view {
  padding: 16px;
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
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
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

.action-buttons {
  display: flex;
  border-radius: 28px;
  background: linear-gradient(135deg, #ff4564, #c8325a);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -3px -3px 8px rgba(255, 255, 255, 0.1),
    inset 0 1px 1px rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.action-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.action-btn::after {
  content: '';
  position: absolute;
  top: 10px;
  bottom: 10px;
  width: 1px;
  background: rgba(255, 255, 255, 0.2);
}

.action-btn.play-btn::after {
  right: 0;
}

.action-btn.shuffle-btn::after {
  display: none;
}

.action-btn:active {
  background: rgba(0, 0, 0, 0.15);
  box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.action-btn.play-btn svg {
  margin-left: 2px;
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
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
  color: rgba(255, 69, 100, 0.4);
}

.empty-state p {
  margin: 0 0 8px 0;
}

.empty-state .hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* No channel prompt */
.no-channel-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 32px 24px;
}

.no-channel-prompt .prompt-icon {
  color: rgba(255, 69, 100, 0.8);
  margin-bottom: 16px;
}

.no-channel-prompt h2 {
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.no-channel-prompt p {
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.no-channel-prompt .setup-btn {
  background: linear-gradient(135deg, #ff4564 0%, #ff6b8a 100%);
  border: none;
  border-radius: 24px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 32px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.no-channel-prompt .setup-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(255, 69, 100, 0.3);
}
</style>
