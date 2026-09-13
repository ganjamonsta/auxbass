<template>
  <div class="search-view">
    <!-- Search Bar -->
    <div class="search-bar-wrapper">
      <SearchBar
        v-model="searchQuery"
        placeholder="Поиск по трекам, тегам #, артистам, плейлистам..."
        :loading="isLoading"
        @input="debouncedSearch"
        @clear="handleClear"
      />
    </div>

    <!-- Filter chips (when query is active OR when a tab filter is active) -->
    <div v-if="searchQuery.trim() || activeFilter !== 'all'" class="search-type-chips">
      <button 
        v-for="chip in filterChips" 
        :key="chip.id"
        class="type-chip"
        :class="{ active: activeFilter === chip.id }"
        @click="setFilter(chip.id)"
      >
        <span>{{ chip.label }}</span>
        <span v-if="getChipBadge(chip.id)" class="chip-badge">{{ getChipBadge(chip.id) }}</span>
      </button>
    </div>

    <!-- Search Results Mode -->
    <div v-if="searchQuery.trim() || activeFilter === 'soundcloud' || activeFilter === 'spotify'" class="search-results-container">
      <!-- Loading initial search results skeleton -->
      <div v-if="isInitialLoading" class="search-skeleton-list">
        <TrackSkeleton v-for="n in 8" :key="n" />
      </div>

      <template v-else>
        <!-- ==================== TAB: ALL ==================== -->
        <SearchTabAll 
          v-if="activeFilter === 'all'"
          :topTracks="topTracks"
          :totalTracksCount="totalTracksCount"
          :soundcloudResults="soundcloudResults"
          :spotifyResults="spotifyResults"
          :artistsResults="artistsResults"
          :albumsResults="albumsResults"
          :playlistsResults="playlistsResults"
          :importingTrackUrl="importingTrackUrl"
          @switchFilter="activeFilter = $event"
          @playTrack="handlePlayTrack"
          @likeTrack="handleLikeTrack"
          @menu="(e, type, item) => openMenu(type, item, 'search', e)"
          @downloadTrack="handleDirectDownload"
          @hdNotice="handleHdNotice"
          @addToLibrary="handleAddToLibrary"
          @quickPlaySoundCloud="handleQuickPlaySoundCloud"
          @quickAddSoundCloud="handleQuickAddSoundCloud"
          @quickPlaySpotify="handleQuickPlaySpotify"
          @quickAddSpotify="handleQuickAddSpotify"
          @goToArtist="goToArtist"
          @goToAlbum="goToAlbum"
          @goToPlaylist="goToPlaylist"
        />

        <!-- ==================== TAB: TRACKS ==================== -->
        <SearchTabTracks
          v-else-if="activeFilter === 'tracks'"
          :isTracksSearching="isTracksSearching"
          :allTracksList="allTracksList"
          :libraryResults="libraryResults"
          :libraryTotal="libraryTotal"
          :hasMoreLibrary="hasMoreLibrary"
          :isLibraryLoadingMore="isLibraryLoadingMore"
          :friendsResults="friendsResults"
          :friendsTotal="friendsTotal"
          :hasMoreFriends="hasMoreFriends"
          :isFriendsLoadingMore="isFriendsLoadingMore"
          :isFriendsLoading="isFriendsLoading"
          :globalResults="globalResults"
          :globalTotal="globalTotal"
          :hasMoreGlobal="hasMoreGlobal"
          :isGlobalLoadingMore="isGlobalLoadingMore"
          :isGlobalLoading="isGlobalLoading"
          @playTrack="handlePlayTrack"
          @likeTrack="handleLikeTrack"
          @menu="(e, type, item) => openMenu(type, item, 'search', e)"
          @downloadTrack="handleDirectDownload"
          @hdNotice="handleHdNotice"
          @addToLibrary="handleAddToLibrary"
          @loadMoreLibrary="loadMoreLibrary"
          @loadMoreFriends="loadMoreFriends"
          @loadMoreGlobal="loadMoreGlobal"
        />

        <!-- ==================== TAB: ARTISTS ==================== -->
        <SearchTabArtists
          v-else-if="activeFilter === 'artists'"
          :artistsResults="artistsResults"
          :isArtistsSearching="isArtistsSearching"
          @goToArtist="goToArtist"
        />

        <!-- ==================== TAB: SOUNDCLOUD ==================== -->
        <SearchTabSoundCloud
          v-else-if="activeFilter === 'soundcloud'"
          :soundcloudResults="soundcloudResults"
          :searchQuery="searchQuery"
          :scSubTab="scSubTab"
          :isSoundCloudSearching="isSoundCloudSearching"
          :isLoadingMoreSoundCloud="isLoadingMoreSoundCloud"
          :importingTrackUrl="importingTrackUrl"
          :scAccount="scAccount"
          :scLikes="scLikes"
          :filteredScLikes="filteredScLikes"
          :scLikesCursor="scLikesCursor"
          :isScLikesLoading="isScLikesLoading"
          :isLoadingMoreScLikes="isLoadingMoreScLikes"
          :isSearchingDeeperLikes="isSearchingDeeperLikes"
          :isSyncingAllLikes="isSyncingAllLikes"
          :syncJobProgress="syncJobProgress"
          :unimportedLikesCount="unimportedLikesCount"
          @resetToAllSearch="resetToAllSearch"
          @setScSubTab="setScSubTab"
          @loadMoreSoundCloud="loadMoreSoundCloud"
          @quickPlaySoundCloud="handleQuickPlaySoundCloud"
          @quickAddSoundCloud="handleQuickAddSoundCloud"
          @handleSyncAllLikes="handleSyncAllLikes"
          @fetchScLikes="fetchScLikes"
          @clearSearchInput="clearSearchInput"
          @loadAllLikesUntilMatch="loadAllLikesUntilMatch"
          @loadMoreScLikes="loadMoreScLikes"
          @goToSettings="router.push('/settings')"
        />

        <!-- ==================== TAB: SPOTIFY ==================== -->
        <SearchTabSpotify
          v-else-if="activeFilter === 'spotify'"
          :spotifyResults="spotifyResults"
          :searchQuery="searchQuery"
          :spSubTab="spSubTab"
          :isSpotifySearching="isSpotifySearching"
          :isLoadingMoreSpotify="isLoadingMoreSpotify"
          :importingTrackUrl="importingTrackUrl"
          @resetToAllSearch="resetToAllSearch"
          @setSpSubTab="setSpSubTab"
          @loadMoreSpotify="loadMoreSpotify"
          @quickPlaySpotify="handleQuickPlaySpotify"
          @quickAddSpotify="handleQuickAddSpotify"
        />

        <!-- ==================== TAB: ALBUMS ==================== -->
        <SearchTabAlbums
          v-else-if="activeFilter === 'albums'"
          :albumsResults="albumsResults"
          :isAlbumsSearching="isAlbumsSearching"
          @goToAlbum="goToAlbum"
          @menu="(e, type, item) => openMenu(type, item, 'search', e)"
        />

        <!-- ==================== TAB: PLAYLISTS ==================== -->
        <SearchTabPlaylists
          v-else-if="activeFilter === 'playlists'"
          :playlistsResults="playlistsResults"
          :isPlaylistsSearching="isPlaylistsSearching"
          @goToPlaylist="goToPlaylist"
          @menu="(e, type, item) => openMenu(type, item, 'search', e)"
        />

        <!-- Global Empty Results (All categories empty) -->
        <NoResultsBox v-if="noResults" :text="`Ничего не найдено по запросу «${searchQuery}»`" hint="Попробуйте ввести другой тег, название трека, исполнителя или плейлиста" />
      </template>
    </div>

    <!-- ==================== EXPLORE MODE: DYNAMIC TAGS GRID ==================== -->
    <SearchExploreTags
      v-else
      :tagScope="tagScope"
      :loadingTags="loadingTags"
      :tags="tags"
      :displayTags="displayTags"
      @switchScope="switchScope"
      @tagClick="handleTagClick"
      @playTagMix="handlePlayTagMix"
    />

  </div>
</template>

<script setup>
import SearchTabAll from '@/components/search/SearchTabAll.vue'
import SearchTabTracks from '@/components/search/SearchTabTracks.vue'
import SearchTabSoundCloud from '@/components/search/SearchTabSoundCloud.vue'
import SearchTabSpotify from '@/components/search/SearchTabSpotify.vue'
import SearchTabArtists from '@/components/search/SearchTabArtists.vue'
import SearchTabAlbums from '@/components/search/SearchTabAlbums.vue'
import SearchTabPlaylists from '@/components/search/SearchTabPlaylists.vue'
import SearchExploreTags from '@/components/search/SearchExploreTags.vue'
import { ref, computed, watch, onMounted, onUnmounted, onActivated } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useUIStore } from '@/stores/ui'
import { useTasksStore } from '@/stores/tasks'
import { useExternalAccountsStore } from '@/stores/externalAccounts'
import { 
  useContextMenu, 
  useDebouncedSearch, 
  useTrackSearch, 
  useTrackActions, 
  useTrackSync 
} from '@/composables'
import api, { tracksApi, artistsApi, albumsApi, playlistsApi, ingestionApi } from '@/api/client'
import SearchBar from '@/components/ui/SearchBar.vue'
import TrackItem from '@/components/TrackItem.vue'
import ExternalTrackItem from '@/components/ExternalTrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import NoResultsBox from '@/components/NoResultsBox.vue'
import { getCoverUrl, CoverSize, formatDuration } from '@/utils'
import { 
  Music, 
  Hash, 
  Play, 
  Users, 
  Disc3,
  Globe, 
  Folder, 
  ArrowRight,
  ArrowLeft,
  Plus,
  Heart,
  RefreshCw,
  Check,
  CloudDownload,
  ExternalLink,
  Radio,
  Settings,
  FileSpreadsheet,
  Upload,
  Clock
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const uiStore = useUIStore()
const tasksStore = useTasksStore()
const externalAccountsStore = useExternalAccountsStore()
const { openMenu } = useContextMenu()
const { handleDirectDownload, handleHdNotice } = useTrackActions()

// Input & Debounce
const { 
  query: searchQuery, 
  debouncedQuery, 
  search: debouncedSearch, 
  clear: clearSearchInput, 
  setQuery 
} = useDebouncedSearch()

const activeFilter = ref('all')

// ─── 3-Tier Track Search Composable ───
const {
  searchQuery: trackSearchQuery,
  libraryResults,
  friendsResults,
  globalResults,
  isSearching: isTracksSearching,
  isFriendsLoading,
  isGlobalLoading,
  isFriendsLoadingMore,
  isGlobalLoadingMore,
  libraryPage,
  libraryTotal,
  friendsTotal,
  globalTotal,
  hasMoreLibrary,
  hasMoreFriends,
  hasMoreGlobal,
  isLibraryLoadingMore,
  allResults: allTracksList,
  loadMoreLibrary,
  loadMoreFriends,
  loadMoreGlobal,
  clearSearch: clearTrackSearch,
  search: executeTrackSearch
} = useTrackSearch({ perPage: 40 })

// Auto-sync reactive track models
useTrackSync(libraryResults, { isLibraryList: true })
useTrackSync(friendsResults)
useTrackSync(globalResults)

// ─── Artists, Albums & Playlists Search State ───
const artistsResults = ref([])
const albumsResults = ref([])
const playlistsResults = ref([])
const isArtistsSearching = ref(false)
const isAlbumsSearching = ref(false)
const isPlaylistsSearching = ref(false)

// ─── SoundCloud External Search & Likes State ───
const soundcloudResults = ref([])
const isSoundCloudSearching = ref(false)
const isLoadingMoreSoundCloud = ref(false)
const importingTrackUrl = ref(null)

const scSubTab = ref('search') // 'search' | 'likes'
const scAccount = computed(() => externalAccountsStore.scAccount)
const isScAccountLoading = computed(() => externalAccountsStore.loadingSc)
const scLikes = ref([])
const isScLikesLoading = ref(false)
const scLikesCursor = ref(null)
const isLoadingMoreScLikes = ref(false)
const isSyncingAllLikes = ref(false)
const syncJobProgress = ref(null)

const fetchScAccountForSearch = async (force = false) => {
  try {
    await externalAccountsStore.fetchSoundCloud(force)
  } catch (e) {
    console.error('Failed to get SC account:', e)
  }
}

const fetchScLikes = async (reset = true) => {
  if (isScLikesLoading.value) return
  isScLikesLoading.value = true
  try {
    if (reset) {
      scLikesCursor.value = null
    }
    const res = await ingestionApi.getSoundCloudLikes({ limit: 40 })
    scLikes.value = res.data?.items || []
    scLikesCursor.value = res.data?.next_cursor || null
    if (res.data?.account) {
      externalAccountsStore.setSoundCloudAccount(res.data.account)
    }
  } catch (e) {
    console.error('Failed to fetch SC likes:', e)
    if (e.response?.status !== 404) {
      uiStore.toast?.error('Ошибка', e.response?.data?.detail || 'Не удалось загрузить лайки')
    }
  } finally {
    isScLikesLoading.value = false
  }
}

const loadMoreScLikes = async () => {
  if (!scLikesCursor.value || isLoadingMoreScLikes.value) return
  isLoadingMoreScLikes.value = true
  try {
    const res = await ingestionApi.getSoundCloudLikes({ cursor: scLikesCursor.value, limit: 40 })
    const more = res.data?.items || []
    scLikes.value = [...scLikes.value, ...more]
    scLikesCursor.value = res.data?.next_cursor || null
  } catch (e) {
    console.error('Failed to load more likes:', e)
  } finally {
    isLoadingMoreScLikes.value = false
  }
}

const switchToLikesTab = () => {
  scSubTab.value = 'likes'
  if (scLikes.value.length === 0 && scAccount.value?.connected) {
    fetchScLikes(true)
  }
}

const isSearchingDeeperLikes = ref(false)

function isCloseMatch(term, text) {
  if (!term || !text) return false
  if (text.includes(term)) return true

  // Word-by-word comparison
  const words = text.split(/[\s\-_|,./()\[\]]+/).filter(w => w.length >= 4)
  for (const word of words) {
    if (word.includes(term) || term.includes(word)) return true
    if (term.length >= 5 && Math.abs(term.length - word.length) <= 2) {
      let prev = []
      for (let j = 0; j <= word.length; j++) prev[j] = j
      for (let i = 1; i <= term.length; i++) {
        const curr = [i]
        for (let j = 1; j <= word.length; j++) {
          const cost = term[i - 1] === word[j - 1] ? 0 : 1
          curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        }
        prev = curr
      }
      const maxDist = term.length >= 8 ? 2 : 1
      if (prev[word.length] <= maxDist) return true
    }
  }
  return false
}

const filteredScLikes = computed(() => {
  const q = searchQuery.value?.trim().toLowerCase()
  if (!q) return scLikes.value

  const terms = q.split(/\s+/).filter(Boolean)

  return scLikes.value.filter(track => {
    const title = (track.title || '').toLowerCase()
    const artist = (track.artist || '').toLowerCase()
    const album = (track.album || '').toLowerCase()
    const combined = `${artist} ${title} ${album}`

    return terms.every(term => isCloseMatch(term, combined))
  })
})

const unimportedLikesCount = computed(() => {
  const targetList = searchQuery.value?.trim() ? filteredScLikes.value : scLikes.value
  return targetList.filter(t => !t.in_library).length
})

const loadAllLikesUntilMatch = async () => {
  if (isSearchingDeeperLikes.value || !scLikesCursor.value) return
  isSearchingDeeperLikes.value = true
  try {
    let pages = 0
    while (scLikesCursor.value && pages < 6) {
      pages++
      const res = await ingestionApi.getSoundCloudLikes({ cursor: scLikesCursor.value, limit: 50 })
      const more = res.data?.items || []
      if (more.length === 0) break
      scLikes.value = [...scLikes.value, ...more]
      scLikesCursor.value = res.data?.next_cursor || null
      if (filteredScLikes.value.length > 0 || !scLikesCursor.value) {
        break
      }
    }
    if (filteredScLikes.value.length > 0) {
      uiStore.toast?.success('Найдено', `Найдено треков в лайках: ${filteredScLikes.value.length}`)
    } else if (!scLikesCursor.value) {
      uiStore.toast?.info('Поиск завершён', 'Проверены все доступные лайки вашего профиля')
    }
  } catch (e) {
    console.error('Failed to load deeper SoundCloud likes:', e)
    uiStore.toast?.error('Ошибка', 'Не удалось загрузить следующие страницы лайков')
  } finally {
    isSearchingDeeperLikes.value = false
  }
}

const handleSyncAllLikes = async () => {
  if (isSyncingAllLikes.value) return
  const targetList = searchQuery.value?.trim() ? filteredScLikes.value : scLikes.value
  const toImport = targetList.filter(t => !t.in_library)
  if (toImport.length === 0) {
    uiStore.toast?.info('Синхронизация', 'Все треки из лайков уже в вашей медиатеке!')
    return
  }

  isSyncingAllLikes.value = true
  try {
    const urls = toImport.map(t => t.url)
    const res = await ingestionApi.start(urls[0], urls)
    const jobId = res.data?.id
    uiStore.toast?.success('Синхронизация', `Запущен импорт ${urls.length} треков в медиатеку и Telegram-канал`)

    const pollInterval = setInterval(async () => {
      try {
        const jobRes = await ingestionApi.getJob(jobId)
        const job = jobRes.data
        syncJobProgress.value = job
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          clearInterval(pollInterval)
          isSyncingAllLikes.value = false
          syncJobProgress.value = null
          await fetchScLikes(true)
          libraryStore.fetchTracks({ refresh: true })
          if (job.status === 'completed') {
            uiStore.toast?.success('Готово', `Синхронизировано треков: ${job.processed_tracks}`)
          }
        }
      } catch (err) {
        clearInterval(pollInterval)
        isSyncingAllLikes.value = false
        syncJobProgress.value = null
      }
    }, 2000)
  } catch (e) {
    console.error('Failed to start sync job:', e)
    uiStore.toast?.error('Ошибка', 'Не удалось запустить синхронизацию')
    isSyncingAllLikes.value = false
  }
}

const searchSoundCloud = async (query, limit = 30) => {
  const cleanQ = query.replace(/^#/, '').trim()
  if (!cleanQ || cleanQ.length < 2) {
    soundcloudResults.value = []
    return
  }

  isSoundCloudSearching.value = true
  try {
    const res = await ingestionApi.search(cleanQ, 'soundcloud', limit)
    soundcloudResults.value = res.data || []
  } catch (e) {
    console.error('Failed to search SoundCloud:', e)
    soundcloudResults.value = []
  } finally {
    isSoundCloudSearching.value = false
  }
}

const loadMoreSoundCloud = async () => {
  const cleanQ = searchQuery.value.replace(/^#/, '').trim()
  if (!cleanQ || isLoadingMoreSoundCloud.value) return
  isLoadingMoreSoundCloud.value = true
  try {
    const targetLimit = Math.min(60, soundcloudResults.value.length + 30)
    const res = await ingestionApi.search(cleanQ, 'soundcloud', targetLimit)
    soundcloudResults.value = res.data || []
  } catch (e) {
    console.error('Failed to load more from SoundCloud:', e)
  } finally {
    isLoadingMoreSoundCloud.value = false
  }
}

const handleQuickPlaySoundCloud = async (scTrack) => {
  if (importingTrackUrl.value) return
  importingTrackUrl.value = scTrack.url

  try {
    const res = await ingestionApi.quickImport({
      url: scTrack.url,
      title: scTrack.title,
      artist: scTrack.artist,
      duration: scTrack.duration,
      cover_url: scTrack.cover_url,
      add_to_library: false,
    })

    const track = res.data?.track
    if (track) {
      if (track.in_library) {
        scTrack.in_library = true
      }
      scTrack.already_in_tg = true
      scTrack.track_id = track.id
      playerStore.playTrack(track, [track], 0)
    }
  } catch (e) {
    console.error('Failed to quick play track:', e)
    const errorMsg = e.response?.data?.detail || 'Не удалось загрузить трек'
    uiStore.toast?.error('Ошибка воспроизведения', errorMsg)
  } finally {
    importingTrackUrl.value = null
  }
}

const isTrackInLibrary = (item) => {
  if (!item) return false
  return item.in_library || tasksStore.isTrackCompleted(item.url)
}

const handleQuickAddSoundCloud = (scTrack) => {
  tasksStore.enqueueTrack(scTrack, 'soundcloud')
}

// ─── Spotify External Search & Likes State ───
const spotifyResults = ref([])
const isSpotifySearching = ref(false)
const isLoadingMoreSpotify = ref(false)

const spSubTab = ref('search') // 'search' | 'exportify'
const spAccount = computed(() => externalAccountsStore.spAccount)
const isSpAccountLoading = computed(() => externalAccountsStore.loadingSp)

const fetchSpAccountForSearch = async (force = false) => {
  try {
    await externalAccountsStore.fetchSpotify(force)
  } catch (e) {
    console.error('Failed to get Spotify account:', e)
  }
}

const fetchSpLikes = async (reset = true) => {
  if (isSpLikesLoading.value) return
  isSpLikesLoading.value = true
  try {
    if (reset) {
      spLikesCursor.value = null
    }
    const res = await ingestionApi.getSpotifyLikes({ limit: 40 })
    spLikes.value = res.data?.items || []
    spLikesCursor.value = res.data?.next_cursor || null
    if (res.data?.account) {
      externalAccountsStore.setSpotifyAccount(res.data.account)
    }
  } catch (e) {
    console.error('Failed to fetch Spotify likes:', e)
    if (e.response?.status !== 404) {
      uiStore.toast?.error('Ошибка', e.response?.data?.detail || 'Не удалось загрузить лайки')
    }
  } finally {
    isSpLikesLoading.value = false
  }
}

const loadMoreSpLikes = async () => {
  if (!spLikesCursor.value || isLoadingMoreSpLikes.value) return
  isLoadingMoreSpLikes.value = true
  try {
    const res = await ingestionApi.getSpotifyLikes({ cursor: spLikesCursor.value, limit: 40 })
    const more = res.data?.items || []
    spLikes.value = [...spLikes.value, ...more]
    spLikesCursor.value = res.data?.next_cursor || null
  } catch (e) {
    console.error('Failed to load more Spotify likes:', e)
  } finally {
    isLoadingMoreSpLikes.value = false
  }
}

const switchToSpotifyLikesTab = () => {
  spSubTab.value = 'likes'
  if (spLikes.value.length === 0 && spAccount.value?.connected) {
    fetchSpLikes(true)
  }
}

const unimportedSpLikesCount = computed(() => {
  return spLikes.value.filter(t => !t.in_library).length
})

const handleSyncAllSpLikes = async () => {
  if (isSyncingAllSpLikes.value) return
  const toImport = spLikes.value.filter(t => !t.in_library)
  if (toImport.length === 0) {
    uiStore.toast?.info('Синхронизация', 'Все треки из лайков уже в вашей медиатеке!')
    return
  }

  isSyncingAllSpLikes.value = true
  try {
    const urls = toImport.map(t => t.url)
    const res = await ingestionApi.start(urls[0], urls)
    const jobId = res.data?.id
    uiStore.toast?.success('Синхронизация', `Запущен импорт ${urls.length} треков Spotify в медиатеку и Telegram-канал`)

    const pollInterval = setInterval(async () => {
      try {
        const jobRes = await ingestionApi.getJob(jobId)
        const job = jobRes.data
        syncSpJobProgress.value = job
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          clearInterval(pollInterval)
          isSyncingAllSpLikes.value = false
          syncSpJobProgress.value = null
          await fetchSpLikes(true)
          libraryStore.fetchTracks({ refresh: true })
          if (job.status === 'completed') {
            uiStore.toast?.success('Готово', `Синхронизировано со Spotify: ${job.processed_tracks}`)
          }
        }
      } catch (err) {
        clearInterval(pollInterval)
        isSyncingAllSpLikes.value = false
        syncSpJobProgress.value = null
      }
    }, 2000)
  } catch (e) {
    console.error('Failed to start Spotify sync job:', e)
    uiStore.toast?.error('Ошибка', 'Не удалось запустить синхронизацию')
    isSyncingAllSpLikes.value = false
  }
}

const searchSpotify = async (query, limit = 30) => {
  const cleanQ = query.replace(/^#/, '').trim()
  if (!cleanQ || cleanQ.length < 2) {
    spotifyResults.value = []
    return
  }

  isSpotifySearching.value = true
  try {
    const res = await ingestionApi.search(cleanQ, 'spotify', limit)
    spotifyResults.value = res.data || []
  } catch (e) {
    console.error('Failed to search Spotify:', e)
    spotifyResults.value = []
  } finally {
    isSpotifySearching.value = false
  }
}

const loadMoreSpotify = async () => {
  const cleanQ = searchQuery.value.replace(/^#/, '').trim()
  if (!cleanQ || isLoadingMoreSpotify.value) return
  isLoadingMoreSpotify.value = true
  try {
    const targetLimit = Math.min(60, spotifyResults.value.length + 30)
    const res = await ingestionApi.search(cleanQ, 'spotify', targetLimit)
    spotifyResults.value = res.data || []
  } catch (e) {
    console.error('Failed to load more from Spotify:', e)
  } finally {
    isLoadingMoreSpotify.value = false
  }
}

const handleQuickPlaySpotify = async (spTrack) => {
  if (importingTrackUrl.value) return
  importingTrackUrl.value = spTrack.url

  try {
    const res = await ingestionApi.quickImport({
      url: spTrack.url,
      title: spTrack.title,
      artist: spTrack.artist,
      duration: spTrack.duration,
      cover_url: spTrack.cover_url,
      add_to_library: false,
    })

    const track = res.data?.track
    if (track) {
      if (track.in_library) {
        spTrack.in_library = true
      }
      spTrack.already_in_tg = true
      spTrack.track_id = track.id
      playerStore.playTrack(track, [track], 0)
    }
  } catch (e) {
    console.error('Failed to quick play Spotify track:', e)
    const errorMsg = e.response?.data?.detail || 'Не удалось загрузить трек'
    uiStore.toast?.error('Ошибка воспроизведения', errorMsg)
  } finally {
    importingTrackUrl.value = null
  }
}

const handleQuickAddSpotify = (spTrack) => {
  tasksStore.enqueueTrack(spTrack, 'spotify')
}

// Local database search loading state (fast, < 150ms)
const isLocalSearching = computed(() => {
  return isTracksSearching.value || isArtistsSearching.value || isAlbumsSearching.value || isPlaylistsSearching.value
})

// Combined search loading state:
// When viewing SoundCloud or Spotify tab, reflect external loading state.
// Otherwise reflect local search state so search input spinner never freezes for 3-5s.
const isLoading = computed(() => {
  if (activeFilter.value === 'soundcloud') return isSoundCloudSearching.value
  if (activeFilter.value === 'spotify') return isSpotifySearching.value
  return isLocalSearching.value
})

// Skeletons are only shown while local database search is executing and no results are shown yet
const isInitialLoading = computed(() => {
  return isLocalSearching.value && 
         allTracksList.value.length === 0 && 
         artistsResults.value.length === 0 && 
         albumsResults.value.length === 0 && 
         playlistsResults.value.length === 0
})

// Dynamic Tags state
const tags = ref([])
const loadingTags = ref(false)
const tagScope = ref('library')

const filterChips = [
  { id: 'all', label: 'Все' },
  { id: 'tracks', label: 'Треки' },
  { id: 'soundcloud', label: 'SoundCloud' },
  { id: 'spotify', label: 'Spotify' },
  { id: 'artists', label: 'Артисты' },
  { id: 'albums', label: 'Альбомы' },
  { id: 'playlists', label: 'Плейлисты' },
]

const totalTracksCount = computed(() => {
  const sum = (libraryTotal.value || 0) + (friendsTotal.value || 0) + (globalTotal.value || 0)
  return sum || allTracksList.value.length
})

const getChipBadge = (chipId) => {
  if (chipId === 'tracks') {
    return totalTracksCount.value > 0 ? totalTracksCount.value : null
  }
  if (chipId === 'soundcloud') {
    if (scSubTab.value === 'likes') {
      if (searchQuery.value?.trim()) {
        return filteredScLikes.value.length
      }
      return scLikes.value.length > 0 ? scLikes.value.length : (scAccount.value?.likes_count || null)
    }
    return soundcloudResults.value.length > 0 ? soundcloudResults.value.length : (scAccount.value?.connected ? '★' : null)
  }
  if (chipId === 'spotify') {
    if (spSubTab.value === 'likes' && spLikes.value.length > 0) {
      return spLikes.value.length
    }
    return spotifyResults.value.length > 0 ? spotifyResults.value.length : (spAccount.value?.connected ? '★' : null)
  }
  if (chipId === 'artists') {
    return artistsResults.value.length > 0 ? artistsResults.value.length : null
  }
  if (chipId === 'albums') {
    return albumsResults.value.length > 0 ? albumsResults.value.length : null
  }
  if (chipId === 'playlists') {
    return playlistsResults.value.length > 0 ? playlistsResults.value.length : null
  }
  return null
}

// Top tracks preview for the "All" tab (max 8 items across library, friends, global)
const topTracks = computed(() => {
  const list = []
  const seen = new Set()
  for (const group of [libraryResults.value, friendsResults.value, globalResults.value]) {
    for (const t of group) {
      if (!seen.has(t.id)) {
        seen.add(t.id)
        list.push(t)
        if (list.length >= 8) return list
      }
    }
  }
  return list
})

const noResults = computed(() => {
  if (isLoading.value || isFriendsLoading.value || isGlobalLoading.value) return false
  if (activeFilter.value === 'all') {
    return topTracks.value.length === 0 && artistsResults.value.length === 0 && albumsResults.value.length === 0 && playlistsResults.value.length === 0 && soundcloudResults.value.length === 0 && spotifyResults.value.length === 0
  }
  if (activeFilter.value === 'tracks') {
    return allTracksList.value.length === 0
  }
  if (activeFilter.value === 'soundcloud') {
    return soundcloudResults.value.length === 0
  }
  if (activeFilter.value === 'spotify') {
    return spotifyResults.value.length === 0
  }
  if (activeFilter.value === 'artists') {
    return artistsResults.value.length === 0
  }
  if (activeFilter.value === 'albums') {
    return albumsResults.value.length === 0
  }
  if (activeFilter.value === 'playlists') {
    return playlistsResults.value.length === 0
  }
  return false
})

// Fallback presets if tags API returns empty
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

const getArtistInitials = (artist) => {
  const name = artist?.name || artist?.artist || ''
  return name.slice(0, 2).toUpperCase() || '♪'
}

const getArtistCoverStyle = (artist) => {
  const str = artist?.name || artist?.artist || 'Artist'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue = Math.abs(hash % 360)
  return {
    background: `linear-gradient(135deg, hsl(${hue}, 50%, 30%) 0%, hsl(${(hue + 50) % 360}, 40%, 20%) 100%)`
  }
}

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

const loadTags = async () => {
  loadingTags.value = true
  try {
    const resp = await tracksApi.getTags(tagScope.value, 40)
    const list = resp.data || []
    if (list.length > 0) {
      tags.value = list
    } else if (tagScope.value === 'library') {
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

// ─── Search Execution ───
const goToAlbum = (albumId) => {
  router.push(`/album/${albumId}`)
}

const searchArtistsAndPlaylists = async (query) => {
  const cleanQ = query.replace(/^#/, '').trim()
  if (!cleanQ) {
    artistsResults.value = []
    albumsResults.value = []
    playlistsResults.value = []
    return
  }

  isArtistsSearching.value = true
  isAlbumsSearching.value = true
  isPlaylistsSearching.value = true

  try {
    const [artistsRes, albumsRes, myPlaylistsRes, globalPlaylistsRes] = await Promise.allSettled([
      artistsApi.getGlobal({ search: cleanQ, limit: 30 }),
      albumsApi.getGlobal({ search: cleanQ, limit: 30 }),
      playlistsApi.getAll({ search: cleanQ, limit: 20 }),
      playlistsApi.getGlobal({ search: cleanQ, limit: 20 })
    ])

    // 1. Artists
    if (artistsRes.status === 'fulfilled') {
      artistsResults.value = artistsRes.value.data?.items || []
    } else {
      console.error('Failed to search artists:', artistsRes.reason)
      const all = libraryStore.artists || []
      artistsResults.value = all.filter(a => (a.name || a.artist || '').toLowerCase().includes(cleanQ.toLowerCase()))
    }

    // 2. Albums
    if (albumsRes.status === 'fulfilled') {
      albumsResults.value = albumsRes.value.data?.items || []
    } else {
      console.error('Failed to search albums:', albumsRes.reason)
      albumsResults.value = []
    }

    // 3. Playlists (Personal + Global)
    const myItems = myPlaylistsRes.status === 'fulfilled' ? (myPlaylistsRes.value.data?.items || myPlaylistsRes.value.data || []) : []
    const globalItems = globalPlaylistsRes.status === 'fulfilled' ? (globalPlaylistsRes.value.data?.items || globalPlaylistsRes.value.data || []) : []

    const seen = new Set()
    const combined = []
    for (const pl of [...myItems, ...globalItems]) {
      if (pl?.id && !seen.has(pl.id)) {
        seen.add(pl.id)
        combined.push(pl)
      }
    }
    if (combined.length > 0 || (myPlaylistsRes.status === 'fulfilled' && globalPlaylistsRes.status === 'fulfilled')) {
      playlistsResults.value = combined
    } else {
      const all = libraryStore.playlists || []
      playlistsResults.value = all.filter(p => (p.name || '').toLowerCase().includes(cleanQ.toLowerCase()))
    }
  } finally {
    isArtistsSearching.value = false
    isAlbumsSearching.value = false
    isPlaylistsSearching.value = false
  }
}

const performSearch = (q) => {
  const query = (q || '').trim()
  if (query) {
    const isTagSearch = query.startsWith('#')
    trackSearchQuery.value = query
    executeTrackSearch()
    searchArtistsAndPlaylists(query)

    // Hashtag queries search within catalog tags and should never trigger external web scraping
    if (!isTagSearch) {
      const isOverview = activeFilter.value === 'all'
      // Request 5 items for overview tab so external scraper returns fast; full 30 when in dedicated tab
      const externalLimit = isOverview ? 5 : 30
      if (activeFilter.value === 'all' || activeFilter.value === 'soundcloud') {
        searchSoundCloud(query, externalLimit)
      }
      if (activeFilter.value === 'all' || activeFilter.value === 'spotify') {
        searchSpotify(query, externalLimit)
      }
    } else {
      soundcloudResults.value = []
      spotifyResults.value = []
    }
  } else {
    clearTrackSearch()
    artistsResults.value = []
    albumsResults.value = []
    playlistsResults.value = []
    soundcloudResults.value = []
    spotifyResults.value = []
  }
}

// Watch debounced query from user typing
watch(debouncedQuery, (newVal) => {
  performSearch(newVal)
})

// On-demand external search when switching to dedicated SoundCloud or Spotify tabs
watch(activeFilter, (newFilter) => {
  const query = (searchQuery.value || '').trim()
  if (!query || query.startsWith('#')) return
  if (newFilter === 'soundcloud' && soundcloudResults.value.length < 30) {
    searchSoundCloud(query, 30)
  } else if (newFilter === 'spotify' && spotifyResults.value.length < 30) {
    searchSpotify(query, 30)
  }
})

const handleClear = () => {
  clearSearchInput()
  clearTrackSearch()
  artistsResults.value = []
  albumsResults.value = []
  playlistsResults.value = []
  soundcloudResults.value = []
  spotifyResults.value = []
  if (tags.value.length === 0) {
    loadTags()
  }
  if (route.query.q || route.query.search || route.query.tag || route.query.tab || route.query.mode) {
    router.replace({ path: '/search', query: {} })
  }
}

// ─── Playback & Track Actions ───
const handlePlayTrack = (track, list, index) => {
  playerStore.playTrack(track, list || allTracksList.value, index >= 0 ? index : 0)
}

const handleLikeTrack = async (track) => {
  await libraryStore.toggleLike(track.id)
  track.is_liked = !track.is_liked
}

const handleAddToLibrary = async (track) => {
  try {
    const success = await libraryStore.addToLibrary(track.id)
    if (success) {
      track.in_library = true
      uiStore.toast.success('Добавлено', 'Трек добавлен в вашу библиотеку')
    }
  } catch (e) {
    uiStore.toast.error('Ошибка', 'Не удалось добавить трек')
  }
}

const goToArtist = (name) => {
  if (name) router.push(`/artist/${encodeURIComponent(name)}`)
}

const goToPlaylist = (id) => {
  if (id) router.push(`/playlist/${id}`)
}

const handleTagClick = (tagName) => {
  setQuery(`#${tagName}`, true)
}

const handlePlayTagMix = async (tagName) => {
  setQuery(`#${tagName}`, true)
  try {
    // 1. Try playing from library mix first
    const libRes = await api.get('/library', { params: { search: `#${tagName}`, per_page: 5 } }).catch(() => null)
    if (libRes?.data?.items?.length) {
      await playerStore.playShuffleAll('library', null, null, { search: `#${tagName}` })
      return
    }

    // 2. Otherwise play from global results for this tag
    const globalRes = await tracksApi.getGlobal({ search: `#${tagName}`, per_page: 30 })
    const items = globalRes.data?.items || []
    if (items.length > 0) {
      playerStore.playTrack(items[0], items, 0)
    } else {
      uiStore.toast.info('Тег', `По тегу #${tagName} треков пока нет`)
    }
  } catch (e) {
    console.error('Failed to play tag mix:', e)
  }
}

// ─── Filter & Sub-Tab Navigation ───
const setFilter = (chipId) => {
  activeFilter.value = chipId
  const newQuery = { ...route.query }
  if (chipId === 'soundcloud') {
    newQuery.tab = 'soundcloud'
    newQuery.mode = scSubTab.value || 'search'
    router.replace({ path: '/search', query: newQuery })
  } else if (chipId === 'spotify') {
    newQuery.tab = 'spotify'
    newQuery.mode = spSubTab.value || 'search'
    router.replace({ path: '/search', query: newQuery })
  } else {
    delete newQuery.tab
    delete newQuery.mode
    router.replace({ path: '/search', query: newQuery })
  }
}

const resetToAllSearch = () => {
  activeFilter.value = 'all'
  const newQuery = { ...route.query }
  delete newQuery.tab
  delete newQuery.mode
  router.replace({ path: '/search', query: newQuery })
}

const setScSubTab = (mode) => {
  scSubTab.value = mode
  if (mode === 'likes') {
    switchToLikesTab()
  }
  const newQuery = { ...route.query, tab: 'soundcloud', mode }
  router.replace({ path: '/search', query: newQuery })
}

const setSpSubTab = (mode) => {
  spSubTab.value = mode
  const newQuery = { ...route.query, tab: 'spotify', mode }
  router.replace({ path: '/search', query: newQuery })
}

// ─── Route Synchronization ───
const applyRouteQuery = () => {
  const tagParam = route.query.tag
  const queryParam = route.query.q || route.query.search
  if (route.query.tab === 'soundcloud') {
    activeFilter.value = 'soundcloud'
    if (route.query.mode === 'likes') {
      scSubTab.value = 'likes'
      if (scLikes.value.length === 0) {
        fetchScLikes()
      }
    } else {
      scSubTab.value = 'search'
    }
  } else if (route.query.tab === 'spotify') {
    activeFilter.value = 'spotify'
    if (route.query.mode === 'likes') {
      spSubTab.value = 'likes'
      if (spLikes.value.length === 0) {
        fetchSpLikes()
      }
    } else if (route.query.mode === 'exportify') {
      spSubTab.value = 'exportify'
    } else {
      spSubTab.value = 'search'
    }
  } else if (!route.query.tab) {
    // When navigated to /search without a tab parameter, reset any external provider filter
    if (activeFilter.value === 'soundcloud' || activeFilter.value === 'spotify') {
      activeFilter.value = 'all'
    }
  }

  if (tagParam && typeof tagParam === 'string') {
    const formatted = tagParam.startsWith('#') ? tagParam : `#${tagParam}`
    setQuery(formatted, true)
  } else if (queryParam && typeof queryParam === 'string') {
    setQuery(queryParam, true)
  }
}

const handleResetState = (event) => {
  if (event.detail?.route === '/search') {
    handleClear()
    activeFilter.value = 'all'
    if (Object.keys(route.query).length > 0) {
      router.replace({ path: '/search', query: {} })
    }
  }
}

onMounted(() => {
  const hasInitialQuery = Boolean(route.query.tag || route.query.q || route.query.search)
  if (!hasInitialQuery) {
    loadTags()
  }
  fetchScAccountForSearch()
  fetchSpAccountForSearch()
  applyRouteQuery()
  window.addEventListener('reset-view-state', handleResetState)
})

// Watch route query params for reactive updates (e.g. from tag clicks, browser navigation, tab switches)
watch(
  () => [route.query.tag, route.query.q, route.query.search, route.query.tab, route.query.mode],
  () => {
    applyRouteQuery()
  }
)

onActivated(() => {
  applyRouteQuery()
  fetchScAccountForSearch()
  fetchSpAccountForSearch()
})

onUnmounted(() => {
  window.removeEventListener('reset-view-state', handleResetState)
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--c-text-2, rgba(255, 255, 255, 0.8));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
  font-family: inherit;
}

.type-chip.active {
  background: var(--c-accent, #1db954);
  color: #000;
  border-color: transparent;
}

.chip-badge {
  font-size: 11px;
  background: rgba(0, 0, 0, 0.2);
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 700;
}

.type-chip.active .chip-badge {
  background: rgba(0, 0, 0, 0.25);
  color: #000;
}

/* Results */
.result-section {
  margin-bottom: 28px;
}

.result-header, .section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.header-left, .section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  letter-spacing: -0.01em;
}

.header-icon {
  color: var(--c-accent, #1db954);
}

.result-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text-1, #fff);
  margin: 0;
}

.result-count, .section-count {
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
}

.section-view-all {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--c-text-3, rgba(255, 255, 255, 0.6));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: all 0.2s;
  font-family: inherit;
}

.section-view-all:hover {
  color: var(--c-accent, #1db954);
  transform: translateX(2px);
}

.track-results-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.section-header.friends-section,
.section-header.global-section {
  margin-top: 24px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.section-loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
  font-size: 13px;
}

.load-more-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  margin-top: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--c-accent, #1db954);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.load-more-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Grids for Artists, Albums & Playlists tabs */
.artists-grid, .albums-grid, .playlists-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(136px, 1fr));
  gap: 14px;
  margin-top: 8px;
}

@media (min-width: 768px) {
  .artists-grid, .albums-grid, .playlists-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }
}

.artists-grid .feed-card,
.albums-grid .feed-card,
.playlists-grid .feed-card {
  width: 100%;
  flex: initial;
}

/* Horizontal scroll cards */
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
  transition: transform 0.2s ease;
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
  aspect-ratio: 1 / 1;
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

/* Card Tags */
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.card-tags.center {
  justify-content: center;
}

.card-tag {
  font-size: 10px;
  font-weight: 500;
  color: var(--c-accent, #1db954);
  background: rgba(29, 185, 84, 0.12);
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  letter-spacing: 0.2px;
  line-height: 14px;
}

/* Empty Results */
.no-results-box {
  text-align: center;
  padding: 48px 16px;
  color: var(--c-text-2, rgba(255, 255, 255, 0.7));
}

.no-results-text {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--c-text-1, #fff);
}

.no-results-hint {
  font-size: 13px;
  color: var(--c-text-3, rgba(255, 255, 255, 0.45));
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

/* SoundCloud Search Styles */
.sc-badge {
  background: #ff5500;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.sc-results-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sc-results-list.full-list {
  margin-top: 12px;
}

.sc-track-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.sc-track-item:hover {
  background: rgba(255, 85, 0, 0.08);
  border-color: rgba(255, 85, 0, 0.25);
  transform: translateX(2px);
}

.sc-track-cover {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  background: #18181c;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
}

.sc-track-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sc-track-play {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  color: #ff5500;
}

.sc-track-item:hover .sc-track-play {
  opacity: 1;
}

.sc-track-loading {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-track-info {
  flex: 1;
  min-width: 0;
}

.sc-track-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-track-artist {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-track-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.sc-track-duration {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.sc-add-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-add-btn:hover:not(:disabled) {
  background: #ff5500;
  border-color: #ff5500;
  transform: scale(1.05);
}

.sc-add-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.sc-add-btn.loading {
  background: rgba(255, 85, 0, 0.18);
  border-color: rgba(255, 85, 0, 0.45);
  cursor: wait;
}

.sc-add-btn.queued {
  background: rgba(56, 189, 248, 0.16);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  cursor: default;
}

.sc-add-btn.sp-add:hover:not(:disabled) {
  background: #1db954;
  border-color: #1db954;
}

.sc-add-btn.sp-add.loading {
  background: rgba(29, 185, 84, 0.18);
  border-color: rgba(29, 185, 84, 0.45);
  cursor: wait;
}

.sc-add-btn.sp-add.queued {
  background: rgba(56, 189, 248, 0.16);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  cursor: default;
}

.sc-load-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  margin-bottom: 24px;
}

.sc-load-more-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: rgba(255, 85, 0, 0.12);
  border: 1px solid rgba(255, 85, 0, 0.3);
  border-radius: 12px;
  color: #ff7700;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-load-more-btn:hover:not(:disabled) {
  background: #ff5500;
  color: #fff;
  border-color: #ff5500;
  box-shadow: 0 4px 16px rgba(255, 85, 0, 0.3);
}

.sc-load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.sc-end-notice {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.4);
}

/* ═══════════════════════════════════════════════
   SoundCloud & Spotify Breadcrumb & Sub-tabs
   ═══════════════════════════════════════════════ */
.sc-nav-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 2px 0;
}

.sc-back-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--c-text-1, #fff);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.sc-back-search-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.28);
  color: var(--c-accent, #1db954);
  transform: translateX(-2px);
}

.sc-service-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

.sc-tab-switcher {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sc-subtab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: none;
  color: var(--c-text-3);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-subtab-btn:hover {
  color: var(--c-text-1);
}

.sc-subtab-btn.active {
  background: #ff5500;
  color: #fff;
  box-shadow: 0 2px 10px rgba(255, 85, 0, 0.35);
}

.sc-subtab-count {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
}

.sc-likes-filter-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--c-text-1);
}

.clear-filter-mini-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: #ffaa77;
  font-size: 11px;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.clear-filter-mini-btn:hover {
  background: rgba(255, 85, 0, 0.25);
  color: #fff;
}

.sc-no-results-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.sc-global-fallback-btn {
  background: #ff5500 !important;
  color: #fff !important;
  border-color: #ff5500 !important;
}

.sc-likes-header-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(255, 85, 0, 0.06);
  border: 1px solid rgba(255, 85, 0, 0.2);
  border-radius: 14px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.sc-likes-user-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sc-likes-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 2px solid #ff5500;
  object-fit: cover;
}

.sc-likes-avatar-placeholder {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.2);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sc-likes-user-meta {
  display: flex;
  flex-direction: column;
}

.sc-likes-username {
  font-size: 14px;
  font-weight: 700;
  color: var(--c-text-1);
}

.sc-likes-stats-text {
  font-size: 12px;
  color: var(--c-text-3);
}

.sc-likes-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sc-sync-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: #ff5500;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
  transition: all 0.2s ease;
}

.sc-sync-btn:hover:not(:disabled) {
  background: #ff6611;
  transform: translateY(-1px);
}

.sc-sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sc-refresh-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--c-text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sc-refresh-icon-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sc-sync-progress-banner {
  padding: 10px 14px;
  background: rgba(255, 85, 0, 0.1);
  border: 1px solid rgba(255, 85, 0, 0.25);
  border-radius: 10px;
  margin-bottom: 14px;
}

.sc-sync-info-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--c-text-1);
  margin-bottom: 6px;
}

.sc-sync-msg {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80%;
}

.sc-sync-bar-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.sc-sync-bar-fill {
  height: 100%;
  background: #ff5500;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.sc-track-artist-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sc-track-badges {
  display: flex;
  gap: 4px;
}

.sc-badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  letter-spacing: 0.2px;
}

.sc-badge-pill.in-lib {
  background: rgba(30, 215, 96, 0.15);
  color: #1ed760;
  border: 1px solid rgba(30, 215, 96, 0.3);
}

.sc-badge-pill.in-chan {
  background: rgba(0, 136, 204, 0.15);
  color: #29b6f6;
  border: 1px solid rgba(0, 136, 204, 0.3);
}

.sc-badge-pill.in-tg {
  background: rgba(255, 255, 255, 0.08);
  color: var(--c-text-3);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.sc-added-indicator {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1ed760;
}

.sc-not-connected-banner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  margin-top: 16px;
}

.sc-banner-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 85, 0, 0.12);
  color: #ff5500;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.sc-banner-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text-1);
  margin: 0 0 6px 0;
}

.sc-banner-desc {
  font-size: 13px;
  color: var(--c-text-3);
  max-width: 440px;
  line-height: 1.5;
  margin: 0 0 16px 0;
}

/* Spotify Styling */
.sp-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #1ed760;
  color: #000;
  font-size: 10px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.sp-count {
  background: rgba(30, 215, 96, 0.2);
  color: #1ed760;
}

.sp-sync-btn {
  background: #1ed760 !important;
  color: #000 !important;
  box-shadow: 0 2px 8px rgba(30, 215, 96, 0.3) !important;
}

.sp-sync-btn:hover:not(:disabled) {
  background: #22e668 !important;
}

.sp-progress-banner {
  background: rgba(30, 215, 96, 0.1) !important;
  border-color: rgba(30, 215, 96, 0.25) !important;
}

.sp-bar-fill {
  background: #1ed760 !important;
}

.sp-banner-icon {
  background: rgba(30, 215, 96, 0.12) !important;
  color: #1ed760 !important;
}

.sp-primary {
  background: #1ed760 !important;
  color: #000 !important;
  font-weight: 700 !important;
}

.sp-primary:hover:not(:disabled) {
  background: #22e668 !important;
}

.sp-placeholder {
  color: #1ed760 !important;
}

.sp-header-card {
  border-left: 3px solid #1ed760;
}

/* Exportify View Card */
.sp-exportify-view-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.sp-exportify-header-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(29, 185, 84, 0.08);
  border: 1px solid rgba(29, 185, 84, 0.2);
  border-radius: 16px;
  padding: 20px 24px;
}

.sp-exportify-icon-large {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: rgba(29, 185, 84, 0.16);
  color: #1ed760;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sp-exportify-title {
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
}

.sp-exportify-subtitle {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #a7b1bc;
}

.sp-exportify-steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.sp-step-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sp-step-card.highlight {
  background: rgba(29, 185, 84, 0.06);
  border-color: rgba(29, 185, 84, 0.25);
}

.sp-step-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #1db954;
  color: #000;
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sp-step-card h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #f1f3f5;
}

.sp-step-card p {
  margin: 0;
  font-size: 12px;
  color: #8b929a;
  line-height: 1.4;
}

.sp-ext-link-btn {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #1ed760;
  text-decoration: underline;
  font-size: 13px;
  font-weight: 600;
}

.sp-open-modal-btn {
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #1db954;
  color: #000;
  border: none;
  padding: 9px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
}

.sp-open-modal-btn:hover {
  background: #24d864;
  transform: translateY(-1px);
}
</style>
