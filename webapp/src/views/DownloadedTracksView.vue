<template>
  <div class="downloaded-tracks-view">
    <!-- Hero Header -->
    <div class="hero-header">
      <div class="hero-cover downloaded-cover">
        <HardDrive :size="48" class="downloaded-icon" />
      </div>
      <div class="hero-info">
        <h1 class="hero-title">Скачанные</h1>
        <p class="hero-meta">{{ tracks.length }} треков</p>
      </div>
    </div>

    <!-- Unified Actions with Expandable Search in one row -->
    <div class="hero-actions" :class="{ 'search-active': isSearchOpen }" v-if="tracks.length">
      <div class="action-buttons" v-if="!isSearchOpen">
        <button class="action-btn play-btn" @click="playAll" title="Слушать все">
          <Play :size="20" fill="currentColor" />
        </button>
        <button class="action-btn shuffle-btn" @click="shufflePlay" title="Перемешать">
          <Shuffle :size="18" />
        </button>
      </div>

      <ExpandableSearch
        v-if="tracks.length > 5"
        v-model="searchQuery"
        v-model:open="isSearchOpen"
        placeholder="Поиск по скачанным..."
        title="Поиск по скачанным"
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Track list -->
    <div class="track-list" v-else-if="sortedTracks.length">
      <TrackItem
        v-for="(track, index) in sortedTracks"
        :key="track.id"
        :track="track"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="track.is_liked"
        @click="playTrack(track, index)"
        @like="handleToggleLike(track)"
        @menu="(e) => openMenu('track', track, 'downloaded', e)"
        @download="handleDirectDownload(track)"
        @hdNotice="handleHdNotice"
      />
    </div>

    <!-- Empty search state -->
    <div v-else-if="searchQuery" class="empty-state search-empty">
      <div class="empty-icon">
        <Search :size="48" />
      </div>
      <p>Ничего не найдено по запросу «{{ searchQuery }}»</p>
      <button type="button" class="btn-global-search" @click="goToGlobalSearch">
        <Search :size="16" />
        <span>Искать в глобальном поиске</span>
      </button>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <HardDrive :size="48" />
      </div>
      <p>Нет скачанных треков</p>
      <p class="hint">Включите автокэширование в Настройках, чтобы слушать музыку без интернета</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useContextMenu } from '@/composables/useContextMenu'
import { useTrackActions, usePlaybackActions, useTrackSync } from '@/composables'
import { getAllCachedTracks } from '@/utils/audioCacheDb'
import TrackItem from '@/components/TrackItem.vue'
import ExpandableSearch from '@/components/ui/ExpandableSearch.vue'
import { HardDrive, Play, Shuffle, Search } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

// Unified track actions
const { handleDirectDownload, handleHdNotice } = useTrackActions()

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()

const rawTracks = ref([])
const loading = ref(true)
const searchQuery = ref('')
const isSearchOpen = ref(false)

const goToGlobalSearch = () => {
  const q = searchQuery.value.trim()
  if (q) {
    router.push({ path: '/search', query: { q } })
  }
}

const tracks = computed(() => rawTracks.value)

// Sync track array with global track events
useTrackSync(rawTracks)

const sortedTracks = computed(() => {
  let list = [...tracks.value]
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase().replace(/^#/, '')
    list = list.filter(t => 
      t.title?.toLowerCase().includes(q) || 
      t.artist?.toLowerCase().includes(q) ||
      t.album?.toLowerCase().includes(q)
    )
  }
  return list
})

// Unified playback actions
const { playAll, shufflePlay, playTrack } = usePlaybackActions(sortedTracks)

const handleToggleLike = async (track) => {
  try {
    if (track.is_liked) {
      await libraryStore.unlikeTrack(track.id)
      track.is_liked = false
    } else {
      await libraryStore.likeTrack(track.id)
      track.is_liked = true
    }
  } catch (_) {}
}

const loadCachedTracks = async () => {
  try {
    rawTracks.value = await getAllCachedTracks()
  } catch (e) {
    console.error('Failed to load cached tracks:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCachedTracks()
  window.addEventListener('cache-updated', loadCachedTracks)
})

onUnmounted(() => {
  window.removeEventListener('cache-updated', loadCachedTracks)
})
</script>

<style scoped>
.downloaded-tracks-view {
  padding: 16px;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  min-height: 44px;
}

.hero-actions.search-active {
  justify-content: stretch;
}

.downloaded-cover {
  background: linear-gradient(135deg, #132b20 0%, #181818 100%);
  border: 1px solid rgba(29, 185, 84, 0.2);
  box-shadow: 
    6px 6px 14px var(--sh-dark),
    -3px -3px 8px var(--sh-light),
    0 0 24px rgba(29, 185, 84, 0.15);
}

.downloaded-icon {
  color: var(--c-accent);
  filter: drop-shadow(0 0 10px rgba(29, 185, 84, 0.6));
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
  color: rgba(29, 185, 84, 0.4);
}

.empty-state p {
  margin: 0 0 8px 0;
}

.empty-state .hint {
  font-size: 13px;
  color: var(--c-text-3);
}

.loading {
  display: flex;
  justify-content: center;
  padding: 48px 16px;
}
</style>
