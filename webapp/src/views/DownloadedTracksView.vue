<template>
  <div class="downloaded-tracks-view">
    <!-- Hero Header -->
    <div class="hero-header">
      <div class="hero-cover downloaded-cover">
        <HardDrive :size="48" class="downloaded-icon" />
      </div>
      <div class="hero-info">
        <h1 class="hero-title">Скачанные</h1>
        <p class="hero-meta">
          <span class="meta-item">{{ tracks.length }} треков</span>
          <span class="meta-dot" v-if="totalBytes > 0">•</span>
          <span class="meta-item" v-if="totalBytes > 0">{{ formatBytes(totalBytes) }}</span>
          <span class="meta-dot">•</span>
          <span class="meta-badge">Офлайн</span>
        </p>
      </div>
    </div>

    <!-- Hero Actions -->
    <div class="hero-actions" v-if="tracks.length">
      <div class="controls-group">
        <!-- Primary Play All Button -->
        <button class="ctrl-btn ctrl-play-btn" @click="playAll" title="Слушать все">
          <Play :size="22" fill="currentColor" />
        </button>
        <!-- Shuffle Play Button -->
        <button class="ctrl-btn ctrl-shuffle-btn" @click="shufflePlay" title="Перемешать">
          <Shuffle :size="20" />
        </button>
      </div>

      <!-- Minimalist Clear Cache Icon Button -->
      <button 
        class="ctrl-btn ctrl-clear-btn" 
        @click="handleClearAll"
        title="Очистить все скачанные треки"
      >
        <Trash2 :size="18" />
      </button>
    </div>

    <!-- Search bar (when tracks exist) -->
    <div class="search-section" v-if="tracks.length > 3">
      <SearchBar
        v-model="searchQuery"
        placeholder="Поиск по скачанным трекам..."
      />
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
    </div>

    <!-- Track list -->
    <div class="track-list" v-else-if="filteredTracks.length">
      <TrackItem
        v-for="(track, index) in filteredTracks"
        :key="track.id"
        :track="track"
        :isPlaying="playerStore.currentTrack?.id === track.id"
        :isLiked="track.is_liked"
        @click="playTrack(track, index)"
        @like="handleLikeTrack(track)"
        @menu="(e) => openMenu('track', track, 'downloaded', e)"
      />
    </div>

    <!-- Search empty state -->
    <div v-else-if="tracks.length && !filteredTracks.length" class="empty-state">
      <p>Ничего не найдено по запросу «{{ searchQuery }}»</p>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-icon">
        <HardDrive :size="48" />
      </div>
      <h3>Нет скачанных треков</h3>
      <p class="hint">Включите автокэширование в Настройках и слушайте музыку — треки автоматически сохранятся сюда для прослушивания без интернета</p>
      <button class="go-settings-btn" @click="router.push('/settings')">
        Настройки кэша
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { useLibraryStore } from '@/stores/library'
import { useContextMenu } from '@/composables/useContextMenu'
import { getAllCachedTracks, getCacheStats, clearAllCache } from '@/utils/audioCacheDb'
import { clearAudioCache } from '@/stores/playerCache'
import TrackItem from '@/components/TrackItem.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import { HardDrive, Play, Shuffle, Trash2 } from 'lucide-vue-next'

const router = useRouter()
const playerStore = usePlayerStore()
const libraryStore = useLibraryStore()
const { openMenu } = useContextMenu()

const tracks = ref([])
const totalBytes = ref(0)
const loading = ref(true)
const searchQuery = ref('')

const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 МБ'
  const mb = bytes / (1024 * 1024)
  if (mb < 1024) return `${mb.toFixed(1)} МБ`
  return `${(mb / 1024).toFixed(1)} ГБ`
}

const loadTracks = async () => {
  try {
    const [cachedTracks, stats] = await Promise.all([
      getAllCachedTracks(),
      getCacheStats()
    ])
    tracks.value = cachedTracks
    totalBytes.value = stats.totalBytes || 0
  } catch (e) {
    console.error('[Downloaded] Error loading cached tracks:', e)
  } finally {
    loading.value = false
  }
}

const filteredTracks = computed(() => {
  if (!searchQuery.value.trim()) return tracks.value
  const q = searchQuery.value.toLowerCase().trim()
  return tracks.value.filter(t => 
    (t.title && t.title.toLowerCase().includes(q)) || 
    (t.artist && t.artist.toLowerCase().includes(q)) ||
    (t.album && t.album.toLowerCase().includes(q))
  )
})

const playTrack = (track, index) => {
  playerStore.playTrack(track, filteredTracks.value)
}

const playAll = () => {
  if (!tracks.value.length) return
  playerStore.playTrack(tracks.value[0], tracks.value)
}

const shufflePlay = () => {
  if (!tracks.value.length) return
  playerStore.playShuffled(tracks.value)
}

const handleLikeTrack = async (track) => {
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

const handleClearAll = async () => {
  if (!confirm('Удалить все скачанные треки из памяти?')) return
  try {
    await clearAudioCache()
    await loadTracks()
  } catch (e) {
    console.error('Error clearing downloaded tracks:', e)
  }
}

onMounted(() => {
  loadTracks()
  window.addEventListener('cache-updated', loadTracks)
})

onUnmounted(() => {
  window.removeEventListener('cache-updated', loadTracks)
})
</script>

<style scoped>
.downloaded-tracks-view {
  padding: var(--sp-4);
  max-width: 900px;
  margin: 0 auto;
  min-height: 100%;
  box-sizing: border-box;
}

/* ─── Hero Header ─── */
.hero-header {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  margin-bottom: var(--sp-4);
}

.hero-cover.downloaded-cover {
  width: 96px;
  height: 96px;
  min-width: 96px;
  border-radius: var(--r-md);
  background: linear-gradient(135deg, #10b981 0%, #047857 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
  color: #ffffff;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0;
  letter-spacing: -0.5px;
}

.hero-meta {
  font-size: 13px;
  color: var(--c-text-2);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  flex-wrap: wrap;
}

.meta-dot {
  color: var(--c-text-3);
}

.meta-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--r-full);
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* ─── Hero Actions ─── */
.hero-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--sp-4);
  padding: 0 2px;
}

.controls-group {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.ctrl-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
}

/* Primary round Play All button */
.ctrl-play-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000000;
  box-shadow: 0 4px 16px rgba(29, 185, 84, 0.4);
}

.ctrl-play-btn svg {
  margin-left: 2px;
}

.ctrl-play-btn:hover {
  transform: scale(1.06);
  background: var(--c-accent-light, #1ed760);
  box-shadow: 0 6px 20px rgba(29, 185, 84, 0.55);
}

.ctrl-play-btn:active {
  transform: scale(0.95);
}

/* Round Shuffle button */
.ctrl-shuffle-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--c-bg-3, #242424);
  color: var(--c-text-2, #b3b3b3);
  border: 1px solid var(--c-border, rgba(255, 255, 255, 0.08));
}

.ctrl-shuffle-btn:hover {
  color: var(--c-accent, #1db954);
  border-color: rgba(29, 185, 84, 0.35);
  background: var(--c-bg-4, #2a2a2a);
  transform: scale(1.05);
}

.ctrl-shuffle-btn:active {
  transform: scale(0.95);
}

/* Minimalist round clear button */
.ctrl-clear-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--c-bg-3, #242424);
  color: var(--c-text-3, #888);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.ctrl-clear-btn:hover {
  color: #ff5252;
  background: rgba(255, 82, 82, 0.12);
  border-color: rgba(255, 82, 82, 0.3);
  transform: scale(1.05);
}

.ctrl-clear-btn:active {
  transform: scale(0.95);
}

/* ─── Search ─── */
.search-section {
  margin-bottom: var(--sp-4);
}

/* ─── Track List ─── */
.track-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ─── Empty & Loading ─── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--sp-8) var(--sp-4);
  color: var(--c-text-2);
}

.empty-icon {
  margin-bottom: var(--sp-3);
  opacity: 0.4;
  color: #10b981;
}

.empty-state h3 {
  color: var(--c-text-1);
  margin: 0 0 var(--sp-2);
}

.empty-state .hint {
  font-size: 13px;
  max-width: 340px;
  line-height: 1.5;
  margin: 0 0 var(--sp-4);
  color: var(--c-text-3);
}

.go-settings-btn {
  background: var(--c-bg-3);
  border: 1px solid var(--c-border);
  color: var(--c-text-1);
  border-radius: var(--r-sm);
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.go-settings-btn:hover {
  background: var(--c-bg-4);
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--sp-8);
}
</style>
