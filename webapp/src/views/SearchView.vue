<template>
  <div class="search-view">
    <!-- Search Bar -->
    <div class="search-bar-wrapper">
      <SearchBar
        v-model="searchQuery"
        placeholder="Треки, артисты, плейлисты..."
        @input="debouncedSearch"
        @clear="handleClear"
      />
    </div>

    <!-- Filter chips (when query or genre active) -->
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
      <!-- Loading indicator -->
      <div v-if="loading" class="search-loading">
        <div class="spinner"></div>
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
              v-for="(track, index) in filteredTracks.slice(0, activeFilter === 'tracks' ? 50 : 6)"
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
          <p class="no-results-hint">Попробуйте ввести имя артиста или другое название трека</p>
        </div>
      </template>
    </div>

    <!-- Empty/Explore Mode: Genres & Quick Browse -->
    <div v-else class="search-explore-container">
      <h2 class="explore-heading">Обзор жанров</h2>
      <div class="genres-grid">
        <div 
          v-for="genre in genreTiles" 
          :key="genre.name"
          class="genre-tile"
          :style="{ background: genre.bg }"
          @click="handleGenreClick(genre.name)"
        >
          <span class="genre-name">{{ genre.name }}</span>
          <div class="genre-card-icon">
            <component :is="genre.icon" :size="32" />
          </div>
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
import SearchBar from '@/components/ui/SearchBar.vue'
import TrackItem from '@/components/TrackItem.vue'
import { getCoverUrl, CoverSize } from '@/utils'
import { 
  Music, 
  Disc3, 
  Radio, 
  Headphones, 
  Flame, 
  Sparkles, 
  Zap, 
  Volume2 
} from 'lucide-vue-next'

const router = useRouter()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()

const { query: searchQuery, debouncedQuery, search: debouncedSearch, clear: handleClear } = useDebouncedSearch()
const activeFilter = ref('all')
const loading = ref(false)

const filterChips = [
  { id: 'all', label: 'Все' },
  { id: 'tracks', label: 'Треки' },
  { id: 'artists', label: 'Артисты' },
  { id: 'playlists', label: 'Плейлисты' },
]

const genreTiles = [
  { name: 'Поп', bg: 'linear-gradient(135deg, #ec4899 0%, #be185d 100%)', icon: Sparkles },
  { name: 'Хип-хоп', bg: 'linear-gradient(135deg, #f59e0b 0%, #b45309 100%)', icon: Flame },
  { name: 'Рок', bg: 'linear-gradient(135deg, #ef4444 0%, #991b1b 100%)', icon: Zap },
  { name: 'Электроника', bg: 'linear-gradient(135deg, #06b6d4 0%, #0e7490 100%)', icon: Headphones },
  { name: 'Инди', bg: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)', icon: Disc3 },
  { name: 'Lo-Fi', bg: 'linear-gradient(135deg, #10b981 0%, #047857 100%)', icon: Radio },
  { name: 'Джаз', bg: 'linear-gradient(135deg, #64748b 0%, #334155 100%)', icon: Music },
  { name: 'Фонк', bg: 'linear-gradient(135deg, #6366f1 0%, #4338ca 100%)', icon: Volume2 },
]

const normalizedQuery = computed(() => {
  return debouncedQuery.value.trim().toLowerCase()
})

const filteredTracks = computed(() => {
  const q = normalizedQuery.value
  if (!q) return []
  const all = libraryStore.tracks || []
  return all.filter(t => 
    t.title?.toLowerCase().includes(q) || 
    t.artist?.toLowerCase().includes(q) ||
    t.album?.toLowerCase().includes(q)
  )
})

const filteredArtists = computed(() => {
  const q = normalizedQuery.value
  if (!q) return []
  const all = libraryStore.artists || []
  return all.filter(a => {
    const name = a.name || a.artist || ''
    return name.toLowerCase().includes(q)
  })
})

const filteredPlaylists = computed(() => {
  const q = normalizedQuery.value
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

const handleGenreClick = async (genreName) => {
  try {
    searchQuery.value = genreName
    debouncedSearch()
  } catch (e) {
    console.error('Failed to search genre:', e)
  }
}

onMounted(async () => {
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

/* Explore: Genres */
.explore-heading {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin-bottom: 14px;
}

.genres-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

@media (min-width: 640px) {
  .genres-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .genres-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.genre-tile {
  height: 96px;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  user-select: none;
}

.genre-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}

.genre-tile:active {
  transform: scale(0.97);
}

.genre-name {
  font-size: 16px;
  font-weight: 800;
  color: #fff;
  z-index: 1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.genre-card-icon {
  position: absolute;
  right: -6px;
  bottom: -6px;
  opacity: 0.35;
  transform: rotate(20deg);
  color: #fff;
}
</style>
