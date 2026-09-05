<template>
  <div class="search-view">
    <!-- Search Bar -->
    <div class="search-bar-wrapper">
      <SearchBar
        v-model="searchQuery"
        placeholder="Поиск по трекам, тегам #, артистам..."
        @input="debouncedSearch"
        @clear="handleClear"
      />
    </div>

    <!-- Filter chips (when query is active) -->
    <div v-if="searchQuery.trim()" class="search-type-chips">
      <button 
        v-for="chip in filterChips" 
        :key="chip.id"
        class="type-chip"
        :class="{ active: activeFilter === chip.id }"
        @click="activeFilter = chip.id"
      >
        {{ chip.label }}
      </button>
    </div>

    <!-- Search Results Mode -->
    <div v-if="searchQuery.trim()" class="search-results-container">
      <!-- Loading search results skeleton -->
      <div v-if="loading" class="search-skeleton-list">
        <TrackSkeleton v-for="n in 6" :key="n" />
      </div>

      <template v-else>
        <!-- Matching Tracks -->
        <section v-if="filteredTracks.length > 0 && (activeFilter === 'all' || activeFilter === 'tracks')" class="result-section">
          <div class="result-header">
            <h3 class="result-title">Треки</h3>
            <span class="result-count">{{ filteredTracks.length }}</span>
          </div>
          <div class="track-results-list">
            <TrackItem
              v-for="(track, index) in filteredTracks.slice(0, activeFilter === 'tracks' ? 50 : 8)"
              :key="track.id"
              :track="track"
              :isPlaying="playerStore.currentTrack?.id === track.id"
              :isLiked="libraryStore.isTrackLiked(track.id)"
              @click="handlePlayTrack(track, filteredTracks, index)"
              @like="libraryStore.toggleLike(track.id)"
              @menu="(e) => openMenu('track', track, 'search', e)"
            />
          </div>
        </section>

        <!-- Matching Artists -->
        <section v-if="filteredArtists.length > 0 && (activeFilter === 'all' || activeFilter === 'artists')" class="result-section">
          <div class="result-header">
            <h3 class="result-title">Артисты</h3>
            <span class="result-count">{{ filteredArtists.length }}</span>
          </div>
          <div class="horizontal-scroll">
            <div 
              v-for="artist in filteredArtists.slice(0, 10)" 
              :key="artist.name || artist.artist"
              class="feed-card artist-card"
              @click="goToArtist(artist.name || artist.artist)"
            >
              <div class="feed-card-cover artist-cover">
                <img 
                  v-if="artist.image_url" 
                  :src="artist.image_url" 
                  alt="" 
                  loading="lazy"
                />
                <span v-else class="artist-initials">
                  {{ (artist.name || artist.artist)?.charAt(0).toUpperCase() }}
                </span>
              </div>
              <div class="feed-card-title">{{ artist.name || artist.artist }}</div>
              <div class="feed-card-subtitle">Исполнитель</div>
            </div>
          </div>
        </section>

        <!-- Matching Playlists -->
        <section v-if="filteredPlaylists.length > 0 && (activeFilter === 'all' || activeFilter === 'playlists')" class="result-section">
          <div class="result-header">
            <h3 class="result-title">Плейлисты</h3>
            <span class="result-count">{{ filteredPlaylists.length }}</span>
          </div>
          <div class="horizontal-scroll">
            <div 
              v-for="pl in filteredPlaylists.slice(0, 8)" 
              :key="pl.id"
              class="feed-card"
              @click="goToPlaylist(pl.id)"
              @contextmenu.prevent="openMenu('playlist', pl, 'search', $event)"
            >
              <div class="feed-card-cover">
                <img 
                  v-if="pl.covers?.length" 
                  :src="getCoverUrl(pl.covers[0], CoverSize.SMALL)" 
                  alt=""
                  loading="lazy"
                />
                <Music v-else :size="32" />
              </div>
              <div class="feed-card-title">{{ pl.name }}</div>
              <div class="feed-card-subtitle">{{ pl.track_count }} треков</div>
            </div>
          </div>
        </section>

        <!-- Empty Results -->
        <div v-if="noResults" class="no-results-box">
          <p class="no-results-text">Ничего не найдено по запросу «{{ searchQuery }}»</p>
          <p class="no-results-hint">Попробуйте ввести другой тег, название трека или артиста</p>
        </div>
      </template>
    </div>

    <!-- Empty/Explore Mode: Dynamic Tags Grid -->
    <div v-else class="search-explore-container">
      <div class="explore-header">
        <div class="explore-title-row">
          <div class="title-with-icon">
            <Hash :size="20" class="explore-icon" />
            <h2 class="explore-heading">Обзор по тегам</h2>
          </div>
          <!-- Scope switcher -->
          <div class="tag-scope-tabs">
            <button 
              class="scope-tab" 
              :class="{ active: tagScope === 'library' }"
              @click="switchScope('library')"
            >
              Мои теги
            </button>
            <button 
              class="scope-tab" 
              :class="{ active: tagScope === 'global' }"
              @click="switchScope('global')"
            >
              Все теги
            </button>
          </div>
        </div>
        <p class="explore-subheading">Нажмите на любой тег, чтобы открыть подборку музыки</p>
      </div>

      <!-- Loading tags skeleton -->
      <div v-if="loadingTags && tags.length === 0" class="tags-loading-grid">
        <div v-for="n in 8" :key="n" class="tag-tile-skeleton">
          <div class="skeleton-tag-title"></div>
          <div class="skeleton-tag-count"></div>
        </div>
      </div>

      <!-- Tags Grid -->
      <div v-else class="tags-grid">
        <div 
          v-for="tag in displayTags" 
          :key="tag.name"
          class="tag-tile"
          :style="{ background: getTagGradient(tag.name) }"
          @click="handleTagClick(tag.name)"
        >
          <div class="tag-info">
            <span class="tag-name">#{{ tag.name }}</span>
            <span v-if="tag.track_count > 0" class="tag-count">
              {{ tag.track_count }} {{ formatTrackCount(tag.track_count) }}
            </span>
          </div>

          <!-- Decorative Hash watermark -->
          <div class="tag-watermark">
            <Hash :size="48" stroke-width="2.5" />
          </div>

          <!-- Quick play mix button -->
          <button 
            v-if="tag.track_count > 0"
            class="tag-play-btn"
            @click.stop="handlePlayTagMix(tag.name)"
            title="Слушать микс по тегу"
          >
            <Play :size="16" fill="currentColor" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { useDebouncedSearch } from '@/composables'
import { tracksApi } from '@/api/client'
import SearchBar from '@/components/ui/SearchBar.vue'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import { getCoverUrl, CoverSize } from '@/utils'
import { 
  Music, 
  Hash, 
  Play 
} from 'lucide-vue-next'

const router = useRouter()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()

const { query: searchQuery, debouncedQuery, search: debouncedSearch, clear: handleClear } = useDebouncedSearch()
const activeFilter = ref('all')
const loading = ref(false)

// Dynamic Tags state
const tags = ref([])
const loadingTags = ref(false)
const tagScope = ref('library')

const filterChips = [
  { id: 'all', label: 'Все' },
  { id: 'tracks', label: 'Треки' },
  { id: 'artists', label: 'Артисты' },
  { id: 'playlists', label: 'Плейлисты' },
]

// Fallback popular tags if none exist yet
const fallbackPresets = [
  { name: 'phonk', track_count: 0 },
  { name: 'dnb', track_count: 0 },
  { name: 'lo-fi', track_count: 0 },
  { name: 'rock', track_count: 0 },
  { name: 'ambient', track_count: 0 },
  { name: 'hiphop', track_count: 0 },
  { name: 'synthwave', track_count: 0 },
  { name: 'chill', track_count: 0 },
  { name: 'nightdrive', track_count: 0 },
  { name: 'indie', track_count: 0 },
  { name: 'electronic', track_count: 0 },
  { name: 'workout', track_count: 0 },
]

const displayTags = computed(() => {
  if (tags.value.length > 0) return tags.value
  return fallbackPresets
})

// Deterministic vibrant HSL gradient generator for tags
const getTagGradient = (name) => {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const h1 = Math.abs(hash % 360)
  const h2 = (h1 + 38) % 360
  return `linear-gradient(135deg, hsl(${h1}, 75%, 40%) 0%, hsl(${h2}, 80%, 25%) 100%)`
}

const formatTrackCount = (count) => {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod100 >= 11 && mod100 <= 19) return 'треков'
  if (mod10 === 1) return 'трек'
  if (mod10 >= 2 && mod10 <= 4) return 'трека'
  return 'треков'
}

const loadTags = async () => {
  loadingTags.value = true
  try {
    const resp = await tracksApi.getTags(tagScope.value, 40)
    const list = resp.data || []
    if (list.length > 0) {
      tags.value = list
    } else if (tagScope.value === 'library') {
      // If library has no tags yet, fall back to global tags
      const globalResp = await tracksApi.getTags('global', 40)
      tags.value = globalResp.data || []
    }
  } catch (e) {
    console.error('Failed to load tags:', e)
  } finally {
    loadingTags.value = false
  }
}

const switchScope = async (scope) => {
  if (tagScope.value === scope) return
  tagScope.value = scope
  tags.value = []
  await loadTags()
}

const normalizedQuery = computed(() => {
  return debouncedQuery.value.trim().toLowerCase()
})

const filteredTracks = computed(() => {
  const q = normalizedQuery.value
  if (!q) return []
  const cleanQ = q.replace(/^#/, '').trim()
  const all = libraryStore.tracks || []
  return all.filter(t => {
    const titleMatch = t.title?.toLowerCase().includes(cleanQ)
    const artistMatch = t.artist?.toLowerCase().includes(cleanQ)
    const albumMatch = t.album?.toLowerCase().includes(cleanQ)
    const tagMatch = t.tags && t.tags.some(tag => {
      const tagName = (typeof tag === 'string' ? tag : tag?.tag || tag?.name || '').toLowerCase().replace(/^#/, '')
      return tagName.includes(cleanQ)
    })
    return titleMatch || artistMatch || albumMatch || tagMatch
  })
})

const filteredArtists = computed(() => {
  const q = normalizedQuery.value.replace(/^#/, '').trim()
  if (!q) return []
  const all = libraryStore.artists || []
  return all.filter(a => {
    const name = a.name || a.artist || ''
    return name.toLowerCase().includes(q)
  })
})

const filteredPlaylists = computed(() => {
  const q = normalizedQuery.value.replace(/^#/, '').trim()
  if (!q) return []
  const all = libraryStore.playlists || []
  return all.filter(p => p.name?.toLowerCase().includes(q))
})

const noResults = computed(() => {
  return filteredTracks.value.length === 0 && 
         filteredArtists.value.length === 0 && 
         filteredPlaylists.value.length === 0
})

const handlePlayTrack = (track, list, index) => {
  playerStore.playTrack(track, list, index >= 0 ? index : 0)
}

const goToArtist = (name) => {
  router.push(`/artist/${encodeURIComponent(name)}`)
}

const goToPlaylist = (id) => {
  router.push(`/playlist/${id}`)
}

const handleTagClick = (tagName) => {
  searchQuery.value = `#${tagName}`
  debouncedSearch()
}

const handlePlayTagMix = (tagName) => {
  searchQuery.value = `#${tagName}`
  debouncedSearch()
  setTimeout(() => {
    if (filteredTracks.value.length > 0) {
      playerStore.playTrack(filteredTracks.value[0], filteredTracks.value, 0)
    }
  }, 150)
}

onMounted(async () => {
  loadTags()
  if (!libraryStore.tracks?.length) {
    libraryStore.fetchTracks()
  }
  if (!libraryStore.artists?.length) {
    libraryStore.fetchArtists()
  }
  if (!libraryStore.playlists?.length) {
    libraryStore.fetchPlaylists()
  }
})
</script>

<style scoped>
.search-view {
  padding: 12px 16px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.search-bar-wrapper {
  margin-bottom: 12px;
}

/* Type filter chips */
.search-type-chips {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.search-type-chips::-webkit-scrollbar {
  display: none;
}

.type-chip {
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--c-text-2, rgba(255, 255, 255, 0.8));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
  font-family: inherit;
}

.type-chip.active {
  background: var(--c-accent, #1db954);
  color: #000;
}

/* Results */
.result-section {
  margin-bottom: 24px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.result-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
}

.result-count {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.track-results-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.no-results-box {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.no-results-text {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}

.no-results-hint {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
}

/* Explore: Tags Header */
.explore-header {
  margin-bottom: 16px;
}

.explore-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.explore-icon {
  color: var(--c-accent, #1db954);
}

.explore-heading {
  font-size: 20px;
  font-weight: 800;
  color: var(--c-text-1, #fff);
  margin: 0;
  letter-spacing: -0.01em;
}

.explore-subheading {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin-top: 4px;
}

/* Scope tabs */
.tag-scope-tabs {
  display: flex;
  background: rgba(255, 255, 255, 0.08);
  padding: 3px;
  border-radius: 12px;
  gap: 2px;
}

.scope-tab {
  background: transparent;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.scope-tab.active {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

/* Tags Grid */
.tags-grid, .tags-loading-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

@media (min-width: 640px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

@media (min-width: 1024px) {
  .tags-grid, .tags-loading-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }
}

.tag-tile {
  height: 96px;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.tag-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
}

.tag-tile:active {
  transform: scale(0.97);
}

.tag-info {
  display: flex;
  flex-direction: column;
  z-index: 1;
}

.tag-name {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.tag-count {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 3px;
}

.tag-watermark {
  position: absolute;
  right: -8px;
  bottom: -8px;
  opacity: 0.18;
  transform: rotate(-15deg);
  color: #fff;
  pointer-events: none;
}

.tag-play-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transform: scale(0.85);
  transition: all 0.2s ease;
  z-index: 2;
  backdrop-filter: blur(4px);
}

.tag-tile:hover .tag-play-btn {
  opacity: 1;
  transform: scale(1);
}

.tag-play-btn:hover {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: transparent;
  transform: scale(1.1) !important;
}

/* Loading skeletons */
.search-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-tile-skeleton {
  height: 96px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  padding: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.skeleton-tag-title {
  height: 16px;
  width: 60%;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-tag-count {
  height: 10px;
  width: 35%;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.05);
  animation: pulse 1.5s ease-in-out infinite;
  animation-delay: 0.15s;
}

@keyframes pulse {
  0%, 100% { opacity: 0.35; }
  50% { opacity: 0.75; }
}
</style>
