<template>
  <div class="library-view">
    <!-- No channel - show setup prompt -->
    <div v-if="!authStore.hasChannel" class="no-channel-prompt">
      <div class="prompt-icon">📚</div>
      <h2>Ваша библиотека</h2>
      <p>Подключите Telegram-канал, чтобы сохранять треки и создавать свою коллекцию музыки</p>
      <button class="setup-btn" @click="goToChannelSetup">
        Подключить канал
      </button>
    </div>

    <!-- Has channel - show library -->
    <template v-else>
      <!-- Search bar -->
      <div class="search-section">
        <SearchBar 
          v-model="searchQuery"
          :placeholder="searchPlaceholder"
          @input="debouncedSearch"
          @clear="handleClearSearch"
        />
      </div>

      <!-- Filter Pills (Spotify style) -->
      <div class="library-filter-pills">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          class="filter-pill"
          :class="{ active: currentTabId === tab.id }"
          @click="setTab(tab.id)"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Overview Dashboard View ("Все" without search) -->
      <div v-if="currentTabId === 'overview' && !debouncedQuery" class="overview-dashboard">
        <!-- Top Quick-Access Grid (Spotify 2x3 / 3x2) -->
        <section v-if="loadingQuickAccess" class="quick-access-grid">
          <div v-for="i in 4" :key="i" class="quick-card quick-skeleton">
            <div class="skeleton-thumb"></div>
            <div class="skeleton-info">
              <div class="skeleton-line-title"></div>
              <div class="skeleton-line-sub"></div>
            </div>
          </div>
        </section>

        <section v-else class="quick-access-grid">
          <!-- Liked Songs Tile (Always First) -->
          <div 
            class="quick-card liked-card" 
            @click="goTo('/liked')"
            @contextmenu.prevent="openMenu('liked', { name: 'Понравившиеся', track_count: likedCount }, 'library', $event)"
            v-longpress="(e) => openMenu('liked', { name: 'Понравившиеся', track_count: likedCount }, 'library', e)"
          >
            <div class="quick-card-cover liked-cover-gradient">
              <Heart :size="24" fill="currentColor" />
            </div>
            <div class="quick-card-info">
              <span class="quick-card-title">Понравившиеся</span>
              <span class="quick-card-meta">{{ likedCount }} треков</span>
            </div>
            <button 
              v-if="likedCount > 0" 
              class="quick-play-btn" 
              @click.stop="handlePlayLiked"
              title="Слушать любимые"
            >
              <Play :size="18" fill="currentColor" />
            </button>
          </div>

          <!-- User Top Playlists -->
          <div 
            v-for="playlist in topPlaylists" 
            :key="playlist.id"
            class="quick-card"
            @click="goTo(`/playlist/${playlist.id}`)"
            @contextmenu.prevent="openMenu('playlist', playlist, 'library', $event)"
            v-longpress="(e) => openMenu('playlist', playlist, 'library', e)"
          >
            <div class="quick-card-cover" :style="getPlaylistCoverStyle(playlist)">
              <img 
                v-if="playlist.covers?.length" 
                :src="getCoverUrl(playlist.covers[0], CoverSize.SMALL)" 
                alt="" 
                loading="lazy"
              />
              <Music v-else :size="22" />
            </div>
            <div class="quick-card-info">
              <span class="quick-card-title">{{ playlist.name }}</span>
              <span class="quick-card-meta">{{ playlist.track_count }} треков</span>
            </div>
            <button 
              v-if="playlist.track_count > 0" 
              class="quick-play-btn" 
              @click.stop="handlePlayPlaylist(playlist)"
              title="Слушать плейлист"
            >
              <Play :size="18" fill="currentColor" />
            </button>
          </div>

          <!-- Quick Add Playlist Tile if fewer than 5 playlists -->
          <div 
            v-if="topPlaylists.length < 5" 
            class="quick-card create-card" 
            @click="handleCreatePlaylist"
            @contextmenu.prevent="handleCreatePlaylist"
            v-longpress="handleCreatePlaylist"
          >
            <div class="quick-card-cover create-cover">
              <Plus :size="24" />
            </div>
            <div class="quick-card-info">
              <span class="quick-card-title">Создать плейлист</span>
              <span class="quick-card-meta">Новая подборка</span>
            </div>
          </div>
        </section>

        <!-- Section: Плейлисты (Horizontal Scroll) -->
        <section v-if="loadingPlaylists" class="library-section">
          <div class="section-header">
            <div class="skeleton-section-title"></div>
          </div>
          <div class="horizontal-scroll">
            <div v-for="i in 5" :key="i" class="feed-card-skeleton">
              <div class="skeleton-feed-cover"></div>
              <div class="skeleton-feed-title"></div>
              <div class="skeleton-feed-sub"></div>
            </div>
          </div>
        </section>

        <section v-else-if="allPlaylists.length > 0" class="library-section">
          <div class="section-header">
            <h2 class="section-title">Плейлисты</h2>
            <button class="section-link" @click="setTab('playlists')">Все {{ allPlaylists.length }}</button>
          </div>
          <div class="horizontal-scroll">
            <div 
              v-for="pl in allPlaylists.slice(0, 10)" 
              :key="pl.id" 
              class="feed-card"
              @click="goTo(`/playlist/${pl.id}`)"
              @contextmenu.prevent="openMenu('playlist', pl, 'library', $event)"
              v-longpress="(e) => openMenu('playlist', pl, 'library', e)"
            >
              <div class="feed-card-cover" :style="getPlaylistCoverStyle(pl)">
                <img 
                  v-if="pl.covers?.length" 
                  :src="getCoverUrl(pl.covers[0], CoverSize.SMALL)" 
                  alt="" 
                  loading="lazy"
                />
                <Folder v-else :size="32" />
                <button 
                  v-if="pl.track_count > 0" 
                  class="play-overlay" 
                  @click.stop="handlePlayPlaylist(pl)"
                  title="Слушать"
                >
                  <Play :size="18" fill="currentColor" />
                </button>
              </div>
              <div class="feed-card-title">{{ pl.name }}</div>
              <div class="feed-card-subtitle">{{ pl.track_count }} треков</div>
            </div>
          </div>
        </section>

        <!-- Section: Альбомы (Horizontal Scroll) -->
        <section v-if="loadingAlbums" class="library-section">
          <div class="section-header">
            <div class="skeleton-section-title"></div>
          </div>
          <div class="horizontal-scroll">
            <div v-for="i in 5" :key="i" class="feed-card-skeleton">
              <div class="skeleton-feed-cover"></div>
              <div class="skeleton-feed-title"></div>
              <div class="skeleton-feed-sub"></div>
            </div>
          </div>
        </section>

        <section v-else-if="overviewAlbums.length > 0" class="library-section">
          <div class="section-header">
            <h2 class="section-title">Альбомы</h2>
            <button class="section-link" @click="setTab('albums')">Все {{ albumsTotal || overviewAlbums.length }}</button>
          </div>
          <div class="horizontal-scroll">
            <div 
              v-for="album in overviewAlbums.slice(0, 10)" 
              :key="album.id" 
              class="feed-card"
              @click="goTo(`/album/${album.id}`)"
              @contextmenu.prevent="openMenu('album', album, 'library', $event)"
              v-longpress="(e) => openMenu('album', album, 'library', e)"
            >
              <div class="feed-card-cover">
                <img 
                  v-if="album.cover_url" 
                  :src="getCoverUrl(album.cover_url, CoverSize.SMALL)" 
                  alt="" 
                  loading="lazy"
                />
                <Disc3 v-else :size="32" />
                <button 
                  class="play-overlay" 
                  @click.stop="handlePlayAlbum(album)"
                  title="Слушать альбом"
                >
                  <Play :size="18" fill="currentColor" />
                </button>
              </div>
              <div class="feed-card-title">{{ album.name }}</div>
              <div class="feed-card-subtitle">{{ album.artist || 'Альбом' }}</div>
            </div>
          </div>
        </section>

        <!-- Section: Исполнители (Horizontal Scroll with round avatars) -->
        <section v-if="loadingArtists" class="library-section">
          <div class="section-header">
            <div class="skeleton-section-title"></div>
          </div>
          <div class="horizontal-scroll">
            <div v-for="i in 5" :key="i" class="feed-card-skeleton artist-card-skeleton">
              <div class="skeleton-feed-cover skeleton-circle"></div>
              <div class="skeleton-feed-title"></div>
            </div>
          </div>
        </section>

        <section v-else-if="overviewArtists.length > 0" class="library-section">
          <div class="section-header">
            <h2 class="section-title">Исполнители</h2>
            <button class="section-link" @click="setTab('artists')">Все {{ overviewArtists.length }}</button>
          </div>
          <div class="horizontal-scroll">
            <div 
              v-for="artist in overviewArtists.slice(0, 10)" 
              :key="artist.name" 
              class="feed-card artist-card"
              @click="goTo(`/artist/${encodeURIComponent(artist.name)}`)"
              @contextmenu.prevent="openMenu('artist', artist, 'library', $event)"
              v-longpress="(e) => openMenu('artist', artist, 'library', e)"
            >
              <div class="feed-card-cover artist-cover" :style="getArtistCoverStyle(artist)">
                <img 
                  v-if="artist.image_url" 
                  :src="getCoverUrl(artist.image_url, CoverSize.SMALL)" 
                  alt="" 
                  loading="lazy"
                />
                <span v-else class="artist-initials">{{ getArtistInitials(artist) }}</span>
              </div>
              <div class="feed-card-title">{{ artist.name }}</div>
              <div class="feed-card-subtitle">{{ artist.track_count }} треков</div>
            </div>
          </div>
        </section>

        <!-- Section: Треки (With Shuffle Button and TrackItems) -->
        <section class="library-section tracks-overview-section">
          <div class="section-header">
            <h2 class="section-title">Треки</h2>
            <button class="section-link" @click="setTab('tracks')">
              Все {{ totalTracksCount }}
            </button>
          </div>

          <!-- Shuffle Button Bar -->
          <div class="overview-actions-bar">
            <button 
              class="shuffle-all-btn" 
              @click="handleShuffleAll" 
              :disabled="totalTracksCount === 0 || shuffling"
            >
              <div v-if="shuffling" class="spinner small"></div>
              <Shuffle v-else :size="16" class="shuffle-icon" />
              <span class="shuffle-text">
                <template v-if="shuffling">Загрузка...</template>
                <template v-else-if="totalTracksCount > 0">Перемешать ({{ totalTracksCount }})</template>
                <template v-else>Перемешать</template>
              </span>
            </button>
          </div>

          <!-- Recent Tracks List -->
          <div v-if="loadingTracks && !overviewTracks.length" class="overview-tracks-loading">
            <div v-for="i in 6" :key="i" class="track-item-skeleton">
              <div class="skeleton-thumb"></div>
              <div class="skeleton-text">
                <div class="skeleton-line-title"></div>
                <div class="skeleton-line-sub"></div>
              </div>
            </div>
          </div>

          <div v-else-if="overviewTracks.length > 0" class="overview-tracks-list">
            <TrackItem
              v-for="track in overviewTracks.slice(0, 15)"
              :key="track.id"
              :track="track"
              :isPlaying="playerStore.currentTrack?.id === track.id"
              :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === track.id"
              :isLiked="track.is_liked"
              @click="playTrack(track)"
              @like="handleLikeTrack(track)"
              @menu="(e) => openMenu('track', track, 'library', e)"
              @download="handleDirectDownload(track)"
              @hdNotice="handleHdNotice"
            />

            <!-- View All Tracks Full Button -->
            <button 
              v-if="totalTracksCount > 15" 
              class="view-all-tracks-btn" 
              @click="setTab('tracks')"
            >
              <span>Смотреть все треки ({{ totalTracksCount }})</span>
              <ChevronRight :size="16" />
            </button>
          </div>

          <div v-else class="overview-empty-tracks">
            <Music :size="36" class="empty-icon" />
            <p>В вашей медиатеке пока нет треков</p>
          </div>
        </section>
      </div>

      <!-- Specific Tab or Search Active View -->
      <div v-else class="library-content">
        <component 
          :is="currentTabComponent" 
          :searchQuery="debouncedQuery"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useContextMenu } from '@/composables/useContextMenu'
import { useDebouncedSearch } from '@/composables'
import api from '@/api/client'
import { getCoverUrl, CoverSize } from '@/utils'
import LibraryTracks from '@/components/library/LibraryTracks.vue'
import LibraryAlbums from '@/components/library/LibraryAlbums.vue'
import LibraryArtists from '@/components/library/LibraryArtists.vue'
import LibraryPlaylists from '@/components/library/LibraryPlaylists.vue'
import TrackItem from '@/components/TrackItem.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import { 
  Heart, 
  Play, 
  Plus, 
  Music, 
  Folder, 
  Disc3, 
  Shuffle, 
  ChevronRight 
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const { openMenu } = useContextMenu()

const goToChannelSetup = () => {
  router.push('/settings#channel')
}

// Available tabs
const tabs = [
  { id: 'overview', label: 'Все', placeholder: 'Название или исполнитель...' },
  { id: 'playlists', label: 'Плейлисты', component: LibraryPlaylists, placeholder: 'Поиск плейлистов...' },
  { id: 'albums', label: 'Альбомы', component: LibraryAlbums, placeholder: 'Поиск альбомов...' },
  { id: 'artists', label: 'Артисты', component: LibraryArtists, placeholder: 'Поиск исполнителей...' },
  { id: 'tracks', label: 'Треки', component: LibraryTracks, placeholder: 'Название или исполнитель...' },
]

// Current tab state synced with uiStore
const currentTabId = computed({
  get: () => uiStore.libraryTab || 'overview',
  set: (val) => uiStore.setLibraryTab(val)
})

const setTab = (tabId) => {
  currentTabId.value = tabId
}

const currentTab = computed(() => tabs.find(t => t.id === currentTabId.value) || tabs[0])

const currentTabComponent = computed(() => {
  if (currentTabId.value === 'overview') {
    // If user is searching while on overview, render LibraryTracks with the query
    if (debouncedQuery.value) {
      return LibraryTracks
    }
    return null
  }
  return currentTab.value?.component || LibraryTracks
})

const searchPlaceholder = computed(() => currentTab.value.placeholder)

// Debounced search using composable
const { query: searchQuery, debouncedQuery, search: debouncedSearch, clear: clearSearch, setQuery } = useDebouncedSearch()

// Overview Data State
const loadingQuickAccess = ref(false)
const loadingPlaylists = ref(false)
const loadingAlbums = ref(false)
const loadingArtists = ref(false)
const loadingTracks = ref(false)
const shuffling = ref(false)

const overviewAlbums = ref([])
const albumsTotal = ref(0)

const likedCount = computed(() => libraryStore.likedTracks?.length || 0)
const allPlaylists = computed(() => libraryStore.playlists || [])
const topPlaylists = computed(() => allPlaylists.value.slice(0, 5))
const overviewArtists = computed(() => libraryStore.artists || [])
const overviewTracks = computed(() => libraryStore.tracks || [])
const totalTracksCount = computed(() => libraryStore.total || overviewTracks.value.length)

// Navigation helpers
const goTo = (path) => {
  router.push(path)
}

// Playback handlers
const handlePlayLiked = () => {
  if (libraryStore.likedTracks?.length > 0) {
    playerStore.playTrack(libraryStore.likedTracks[0], libraryStore.likedTracks, 0)
  }
}

const handlePlayPlaylist = async (playlist) => {
  try {
    await playerStore.playShuffleAll('playlist', playlist.id)
  } catch (e) {
    console.error('Failed to play playlist:', e)
  }
}

const handlePlayAlbum = async (album) => {
  try {
    const response = await api.get(`/albums/${album.id}`)
    const albumData = response.data
    const tracks = albumData.full_tracklist?.filter(t => t.in_library) || albumData.tracks || []
    if (tracks.length > 0) {
      playerStore.playTrack(tracks[0], tracks, 0)
    }
  } catch (e) {
    console.error('Failed to play album:', e)
  }
}

const playTrack = (track) => {
  const list = overviewTracks.value
  const idx = list.findIndex(t => t.id === track.id)
  playerStore.playTrack(track, list, idx >= 0 ? idx : 0)
}

const handleLikeTrack = async (track) => {
  await libraryStore.toggleLike(track.id)
  track.is_liked = !track.is_liked
}

const handleShuffleAll = async () => {
  shuffling.value = true
  try {
    await playerStore.playShuffleAll('library')
  } catch (e) {
    console.error('Failed to shuffle library:', e)
  } finally {
    shuffling.value = false
  }
}

const handleDirectDownload = (track) => {
  if (track?.download_url) {
    window.open(track.download_url, '_blank')
  }
}

const handleHdNotice = (info) => {
  uiStore.toast.info(
    info?.track?.title || 'HD трек', 
    info?.message || 'HD версия доступна'
  )
}

const handleCreatePlaylist = async () => {
  if (!authStore.hasChannel) {
    authStore.promptChannelSetup()
    return
  }
  const name = prompt('Название нового плейлиста:')
  if (!name || !name.trim()) return
  const pl = await libraryStore.createPlaylist(name.trim())
  if (pl?.id) {
    router.push(`/playlist/${pl.id}`)
  }
}

// Cover styles
const getPlaylistCoverStyle = (playlist) => {
  if (playlist.covers?.length) return {}
  const str = playlist.name || 'Playlist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 55%, 35%) 0%, hsl(${(hue + 40) % 360}, 45%, 25%) 100%)`
  }
}

const getArtistInitials = (artist) => {
  const name = artist?.name || ''
  return name.slice(0, 2).toUpperCase() || '♪'
}

const getArtistCoverStyle = (artist) => {
  const str = artist?.name || 'Artist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 50%, 30%) 0%, hsl(${(hue + 50) % 360}, 40%, 20%) 100%)`
  }
}

// Fetch Overview Data
const loadOverviewData = async () => {
  // 1. Playlists
  if (!libraryStore.playlists?.length) {
    loadingPlaylists.value = true
    libraryStore.fetchPlaylists().finally(() => {
      loadingPlaylists.value = false
    })
  }

  // 2. Liked
  if (!libraryStore.likedTracks?.length) {
    loadingQuickAccess.value = true
    libraryStore.fetchLikedTracks().finally(() => {
      loadingQuickAccess.value = false
    })
  }

  // 3. Tracks
  if (!libraryStore.tracks?.length) {
    loadingTracks.value = true
    libraryStore.fetchTracks({ limit: 20 }).finally(() => {
      loadingTracks.value = false
    })
  }

  // 4. Artists
  if (!libraryStore.artists?.length) {
    loadingArtists.value = true
    libraryStore.fetchArtists().finally(() => {
      loadingArtists.value = false
    })
  }

  // 5. Albums
  loadingAlbums.value = true
  try {
    const response = await api.get('/albums', { params: { limit: 12 } })
    overviewAlbums.value = response.data?.items || []
    albumsTotal.value = response.data?.total || overviewAlbums.value.length
  } catch (e) {
    console.error('Failed to load overview albums:', e)
  } finally {
    loadingAlbums.value = false
  }
}

// Sync search query from route or external trigger
const applyRouteSearch = (queryOverride) => {
  const queryParam = queryOverride || route.query.search || route.query.q
  if (queryParam && typeof queryParam === 'string') {
    uiStore.setLibraryTab('tracks')
    setQuery(queryParam, true)
  }
}

const handleAppSearch = (event) => {
  const query = event.detail?.query
  if (query) {
    uiStore.setLibraryTab('tracks')
    setQuery(query, true)
  }
}

const handleClearSearch = () => {
  clearSearch()
  if (route.query.search || route.query.q) {
    router.replace({ path: '/library', query: {} })
  }
}

// Watch route search query param changes
watch(
  () => route.query.search || route.query.q,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      if (searchQuery.value !== newVal) {
        uiStore.setLibraryTab('tracks')
        setQuery(newVal, true)
      }
    }
  }
)

// Handle reset state
const handleResetState = (event) => {
  if (event.detail.route === '/library' || event.detail.route === '/') {
    handleClearSearch()
    currentTabId.value = 'overview'
  }
}

onMounted(() => {
  applyRouteSearch()
  loadOverviewData()
  window.addEventListener('reset-view-state', handleResetState)
  window.addEventListener('app-search', handleAppSearch)
})

onActivated(() => {
  applyRouteSearch()
  loadOverviewData()
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
  window.removeEventListener('app-search', handleAppSearch)
})
</script>

<style scoped>
.library-view {
  padding: 16px 16px 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.search-section {
  margin-bottom: 12px;
}

/* ─── Spotify Filter Pills ─── */
.library-filter-pills {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 4px 0 16px;
  margin-bottom: 8px;
}

.library-filter-pills::-webkit-scrollbar {
  display: none;
}

.filter-pill {
  padding: 7px 15px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-2, rgba(255, 255, 255, 0.75));
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  flex-shrink: 0;
  user-select: none;
}

.filter-pill:hover {
  background: rgba(255, 255, 255, 0.14);
  color: var(--c-text-1, #fff);
  transform: translateY(-1px);
}

.filter-pill:active {
  transform: scale(0.96);
}

.filter-pill.active {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: var(--c-accent, #1db954);
  font-weight: 700;
  box-shadow: 0 2px 12px rgba(29, 185, 84, 0.35);
}

/* ─── Quick Access Grid ─── */
.quick-access-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 28px;
}

@media (min-width: 768px) {
  .quick-access-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  overflow: hidden;
  height: 56px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  user-select: none;
  backdrop-filter: blur(8px);
}

.quick-card:hover {
  background: rgba(255, 255, 255, 0.13);
  transform: translateY(-1px);
}

.quick-card:active {
  transform: scale(0.98);
}

.quick-card-cover {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--c-bg-3, #222);
  color: rgba(255, 255, 255, 0.7);
  overflow: hidden;
}

.quick-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.liked-cover-gradient {
  background: linear-gradient(135deg, #450af5 0%, #c4efd9 100%);
  color: #fff;
}

.create-cover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.quick-card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 8px;
}

.quick-card-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.quick-card-meta {
  font-size: 11px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  margin-top: 2px;
}

.quick-play-btn {
  position: absolute;
  right: 10px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
  opacity: 0;
  transform: scale(0.8);
  transition: all 0.2s ease;
  cursor: pointer;
}

.quick-card:hover .quick-play-btn {
  opacity: 1;
  transform: scale(1);
}

@media (max-width: 767px) {
  .quick-play-btn {
    opacity: 0.9;
    transform: scale(0.9);
  }
}

/* ─── Sections ─── */
.library-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
  margin: 0;
}

.section-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.section-link:hover {
  color: var(--c-accent, #1db954);
}

/* ─── Horizontal Scroll ─── */
.horizontal-scroll {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 8px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.horizontal-scroll::-webkit-scrollbar {
  display: none;
}

.feed-card {
  flex: 0 0 136px;
  width: 136px;
  cursor: pointer;
  scroll-snap-align: start;
  user-select: none;
  transition: transform 0.2s;
}

@media (min-width: 768px) {
  .feed-card {
    flex: 0 0 156px;
    width: 156px;
  }
}

.feed-card:hover {
  transform: translateY(-2px);
}

.feed-card:active {
  transform: scale(0.97);
}

.feed-card-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  background: var(--c-bg-2, #181818);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.feed-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.feed-card:hover .feed-card-cover img {
  transform: scale(1.04);
}

.play-overlay {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--c-accent, #1db954);
  color: #000;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
  opacity: 0;
  transform: translateY(6px);
  transition: all 0.2s ease;
  cursor: pointer;
}

.feed-card:hover .play-overlay {
  opacity: 1;
  transform: translateY(0);
}

@media (max-width: 767px) {
  .play-overlay {
    opacity: 0.9;
    transform: translateY(0);
    width: 32px;
    height: 32px;
  }
}

.feed-card-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.feed-card-subtitle {
  font-size: 12px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─── Artist Specific Card ─── */
.artist-card .artist-cover {
  border-radius: 50%;
}

.artist-initials {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
}

.artist-card .feed-card-title,
.artist-card .feed-card-subtitle {
  text-align: center;
}

/* ─── Tracks Section ─── */
.overview-actions-bar {
  margin-bottom: 14px;
}

.shuffle-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--c-accent, #1db954) 0%, #158a3e 100%);
  color: #000;
  border: none;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
  box-shadow: 0 4px 14px rgba(29, 185, 84, 0.35);
}

.shuffle-all-btn:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 6px 18px rgba(29, 185, 84, 0.45);
}

.shuffle-all-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.shuffle-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.overview-tracks-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.view-all-tracks-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  margin-top: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.8));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.view-all-tracks-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--c-text-1, #fff);
  border-color: rgba(255, 255, 255, 0.15);
}

.overview-empty-tracks {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.4));
  font-size: 14px;
  gap: 8px;
}

/* ─── Skeletons ─── */
.quick-skeleton {
  background: rgba(255, 255, 255, 0.04) !important;
  pointer-events: none;
}

.skeleton-thumb {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.08);
  animation: pulse-shimmer 1.5s infinite;
}

.skeleton-info {
  flex: 1;
  padding: 0 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skeleton-line-title {
  height: 12px;
  width: 70%;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  animation: pulse-shimmer 1.5s infinite;
}

.skeleton-line-sub {
  height: 10px;
  width: 40%;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  animation: pulse-shimmer 1.5s infinite;
}

.skeleton-section-title {
  width: 120px;
  height: 18px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  animation: pulse-shimmer 1.5s infinite;
}

.feed-card-skeleton {
  flex: 0 0 136px;
  width: 136px;
}

@media (min-width: 768px) {
  .feed-card-skeleton {
    flex: 0 0 156px;
    width: 156px;
  }
}

.skeleton-feed-cover {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
  animation: pulse-shimmer 1.5s infinite;
}

.skeleton-circle {
  border-radius: 50% !important;
}

.skeleton-feed-title {
  height: 12px;
  width: 80%;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  margin-bottom: 4px;
  animation: pulse-shimmer 1.5s infinite;
}

.skeleton-feed-sub {
  height: 10px;
  width: 50%;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  animation: pulse-shimmer 1.5s infinite;
}

.track-item-skeleton {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
}

.track-item-skeleton .skeleton-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  flex-shrink: 0;
}

.track-item-skeleton .skeleton-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@keyframes pulse-shimmer {
  0% { opacity: 0.5; }
  50% { opacity: 0.9; }
  100% { opacity: 0.5; }
}

.spinner.small {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ─── No channel prompt ─── */
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
  font-size: 64px;
  margin-bottom: 16px;
}

.no-channel-prompt h2 {
  color: var(--c-text-1);
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.no-channel-prompt p {
  color: var(--c-text-2);
  font-size: 15px;
  line-height: 1.5;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.no-channel-prompt .setup-btn {
  background: linear-gradient(135deg, var(--c-accent) 0%, #00c853 100%);
  border: none;
  border-radius: 24px;
  color: #000;
  font-size: 16px;
  font-weight: 600;
  padding: 14px 32px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.no-channel-prompt .setup-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 4px 16px rgba(0, 230, 118, 0.3);
}
</style>
