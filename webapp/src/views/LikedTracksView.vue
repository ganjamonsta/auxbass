<template>
  <div class="liked-tracks-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon">
        <Heart :size="48" />
      </div>
      <h2>Понравившиеся</h2>
      <p>Подключите Telegram-канал, чтобы сохранять понравившиеся треки</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <template v-else>
      <!-- Unified Hero Header -->
      <div class="hero-header">
        <div class="hero-cover liked-cover">
          <Heart :size="48" class="liked-icon" />
        </div>
        <div class="hero-info">
          <h1 class="hero-title">Понравившиеся</h1>
          <p class="hero-meta">{{ tracks.length }} треков</p>
        </div>
      </div>

      <!-- Unified Actions -->
      <div class="hero-actions" v-if="tracks.length">
        <div class="action-buttons">
          <button class="action-btn play-btn" @click="playAll" title="Слушать все">
            <Play :size="20" fill="currentColor" />
          </button>
          <button class="action-btn shuffle-btn" @click="shufflePlay" title="Перемешать">
            <Shuffle :size="18" />
          </button>
        </div>
      </div>

      <!-- Search bar (when tracks exist) -->
      <div class="search-section" v-if="tracks.length > 5">
        <SearchBar
          v-model="searchQuery"
          placeholder="Поиск по понравившимся..."
        />
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
          <Heart :size="48" />
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
import { useTrackActions, usePlaybackActions, useTrackSync } from '@/composables'
import TrackItem from '@/components/TrackItem.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import { Heart, Play, Shuffle } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

// Unified track actions
const { handleDirectDownload, handleHdNotice } = useTrackActions()

const goToChannelSetup = () => {
  router.push('/settings#channel')
}

const tracks = computed(() => libraryStore.likedTracks)
const loading = ref(true)
const searchQuery = ref('')

// Sync liked tracks with global track events
useTrackSync(() => libraryStore.likedTracks)

const sortedTracks = computed(() => {
  let list = [...tracks.value].sort((a, b) => {
    const dateA = new Date(a.liked_at || 0)
    const dateB = new Date(b.liked_at || 0)
    return dateB - dateA
  })
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(t => 
      t.title?.toLowerCase().includes(q) || 
      t.artist?.toLowerCase().includes(q)
    )
  }
  return list
})

// Unified playback actions
const { playAll, shufflePlay, playTrack } = usePlaybackActions(sortedTracks)

const unlikeTrack = async (track) => {
  try {
    await libraryStore.toggleLike(track.id)
  } catch (error) {
    console.error('Failed to unlike track:', error)
  }
}

onMounted(async () => {
  loading.value = true
  await libraryStore.fetchLikedTracks()
  loading.value = false
})
</script>

<style scoped>
.liked-tracks-view {
  padding: 16px;
}

.search-section {
  margin-bottom: 16px;
}

.liked-cover {
  background: linear-gradient(135deg, #2a151b 0%, #181818 100%);
  border: 1px solid rgba(255, 69, 100, 0.2);
  box-shadow: 
    6px 6px 14px var(--sh-dark),
    -3px -3px 8px var(--sh-light),
    0 0 24px rgba(255, 69, 100, 0.15);
}

.liked-icon {
  color: #ff4564;
  filter: drop-shadow(0 0 10px rgba(255, 69, 100, 0.6));
}

.play-btn svg {
  margin-left: 2px;
}

.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2);
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
  color: var(--c-text-3);
}
</style>
