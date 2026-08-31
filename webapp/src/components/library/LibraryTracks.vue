<template>
  <div class="library-tracks">
    <!-- Sort options -->
    <div class="sort-options">
      <button class="shuffle-all-btn" @click="shuffleAll" :disabled="!total || shuffling">
        <template v-if="shuffling">
          <div class="spinner small"></div>
          <span>Загрузка...</span>
        </template>
        <template v-else>
          <Shuffle :size="16" />
          <span>Перемешать ({{ total }})</span>
        </template>
      </button>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Virtual track list (without search) -->
    <div v-if="!searchQuery" class="virtual-tracks-section">
      <VirtualTrackList
        ref="virtualTrackListRef"
        :fetchFn="fetchTracks"
        :pageSize="50"
        :skeletonCount="12"
        :showAlbum="false"
        menuContext="library"
        @click="handleVirtualClick"
        @like="handleLikeTrack"
        @menu="handleVirtualMenu"
        @download="handleDirectDownload"
        @hdNotice="handleHdNotice"
        @update:total="virtualTotal = $event"
      >
        <template #empty>
          <span class="empty-icon"><Music :size="48" /></span>
          <h3>Библиотека пуста</h3>
          <p>Отправьте аудио боту, чтобы добавить треки</p>
        </template>
      </VirtualTrackList>
    </div>

    <!-- Regular track list with search (friends/global sections) -->
    <div v-else class="track-list search-results" ref="trackListRef">
      <!-- Loading state with skeletons -->
      <template v-if="loading && !tracks.length">
        <TrackSkeleton v-for="i in 12" :key="i" />
      </template>
      
      <template v-else>
        <!-- Section: My Library results -->
        <template v-if="tracks.length">
          <div class="section-header">
            <span class="section-title">Моя библиотека</span>
            <span class="section-count">{{ tracks.length }}<template v-if="searchTotal > tracks.length"> из {{ searchTotal }}</template></span>
          </div>
        </template>
        
        <TrackItem
          v-for="track in tracks"
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

        <!-- Load more trigger for my library search infinite scroll -->
        <div v-if="hasMore" ref="loadTriggerRef" class="load-trigger">
          <div v-if="loadingMore" class="loading-more">
            <div class="spinner small"></div>
          </div>
        </div>

        <!-- Load more my tracks button -->
        <button v-if="hasMore" class="load-more-btn" :disabled="loadingMore" @click="loadMore">
          <template v-if="loadingMore">
            <div class="spinner small"></div>
            <span>Загрузка...</span>
          </template>
          <template v-else>
            <span>Показать ещё ({{ tracks.length }} из {{ searchTotal }})</span>
          </template>
        </button>
        
        <!-- Section: Friends' Libraries results -->
        <template v-if="friendsTracks.length">
          <div class="section-header friends-section">
            <span class="section-title"><Users :size="16" /> У друзей</span>
            <span class="section-count">{{ friendsTracks.length }}<template v-if="friendsTotal > friendsTracks.length"> из {{ friendsTotal }}</template></span>
          </div>
          
          <TrackItem
            v-for="track in friendsTracks"
            :key="'friends-' + track.id"
            :track="track"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === track.id"
            :isLiked="track.is_liked"
            :showAddToLibrary="true"
            :inLibrary="track.in_library"
            @click="playFriendsTrack(track)"
            @like="handleLikeTrack(track)"
            @menu="(e) => openMenu('track', track, 'library', e)"
            @download="handleDirectDownload(track)"
            @hdNotice="handleHdNotice"
            @addToLibrary="handleAddToLibrary(track)"
          />

          <!-- Load more friends -->
          <button v-if="hasMoreFriends" class="load-more-btn" :disabled="friendsLoadingMore" @click="loadMoreFriends">
            <template v-if="friendsLoadingMore">
              <div class="spinner small"></div>
              <span>Загрузка...</span>
            </template>
            <template v-else>
              <span>Показать ещё</span>
            </template>
          </button>
        </template>
        
        <!-- Loading friends results -->
        <div v-if="friendsLoading" class="global-loading">
          <div class="spinner small"></div>
          <span>Поиск у друзей...</span>
        </div>
        
        <!-- Section: Global Network results -->
        <template v-if="globalTracks.length">
          <div class="section-header global-section">
            <span class="section-title"><Globe :size="16" /> Общая сеть</span>
            <span class="section-count">{{ globalTracks.length }}<template v-if="globalTotal > globalTracks.length"> из {{ globalTotal }}</template></span>
          </div>
          
          <TrackItem
            v-for="track in globalTracks"
            :key="'global-' + track.id"
            :track="track"
            :isPlaying="playerStore.currentTrack?.id === track.id"
            :isActive="playerStore.isPlaying && playerStore.currentTrack?.id === track.id"
            :isLiked="track.is_liked"
            :showAddToLibrary="true"
            :inLibrary="track.in_library"
            @click="playGlobalTrack(track)"
            @like="handleLikeTrack(track)"
            @menu="(e) => openMenu('track', track, 'library', e)"
            @download="handleDirectDownload(track)"
            @hdNotice="handleHdNotice"
            @addToLibrary="handleAddToLibrary(track)"
          />

          <!-- Load more global -->
          <button v-if="hasMoreGlobal" class="load-more-btn" :disabled="globalLoadingMore" @click="loadMoreGlobal">
            <template v-if="globalLoadingMore">
              <div class="spinner small"></div>
              <span>Загрузка...</span>
            </template>
            <template v-else>
              <span>Показать ещё</span>
            </template>
          </button>
        </template>
        
        <!-- Loading global results -->
        <div v-if="globalLoading" class="global-loading">
          <div class="spinner small"></div>
          <span>Поиск в общей сети...</span>
        </div>
        
        <div v-if="!tracks.length && !friendsTracks.length && !globalTracks.length && !loading && !friendsLoading && !globalLoading" class="empty-state">
          <span class="empty-icon"><Music :size="48" /></span>
          <h3>Ничего не найдено</h3>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useSort, useTrackActions, useTrackSync } from '@/composables'
import { useTrackSearch } from '@/composables/useTrackSearch'
import { useContextMenu } from '@/composables/useContextMenu'
import VirtualTrackList from '@/components/VirtualTrackList.vue'
import TrackItem from '@/components/TrackItem.vue'
import TrackSkeleton from '@/components/TrackSkeleton.vue'
import SortChips from '@/components/SortChips.vue'
import api from '@/api/client'
import { Users, Music, Globe, Shuffle } from 'lucide-vue-next'

// Universal context menu
const { openMenu } = useContextMenu()

// Track actions (download, HD notice)
const { handleDirectDownload, handleHdNotice } = useTrackActions()

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const router = useRouter()
const libraryStore = useLibraryStore()
const playerStore = usePlayerStore()
const authStore = useAuthStore()
const uiStore = useUIStore()

// Sort state (persisted to localStorage)
const { 
  sortBy, 
  sortOrder, 
  currentOption, 
  nextSort, 
  toggleOrder 
} = useSort('library-sort', 'library', { sortBy: 'added_at', sortOrder: 'desc' })

// Virtual track list ref
const virtualTrackListRef = ref(null)
const virtualTotal = ref(0)

const loading = ref(true)
const loadingMore = ref(false)
const shuffling = ref(false)
const tracks = ref([])
const page = ref(1)
const searchTotal = ref(0) // Real total from API during search
const total = computed(() => {
  if (props.searchQuery) {
    return searchTotal.value || (friendsTracks.value.length + globalTracks.value.length)
  }
  return virtualTotal.value
})
const perPage = 50
const loadTriggerRef = ref(null)
let observer = null

const hasMore = computed(() => tracks.value.length < searchTotal.value)

// Unified friends + global search (via composable)
const {
  friendsResults: friendsTracks,
  globalResults: globalTracks,
  isFriendsLoading: friendsLoading,
  isGlobalLoading: globalLoading,
  isFriendsLoadingMore: friendsLoadingMore,
  isGlobalLoadingMore: globalLoadingMore,
  hasMoreFriends,
  hasMoreGlobal,
  friendsTotal,
  globalTotal,
  searchFriendsAndGlobal,
  loadMoreFriends,
  loadMoreGlobal,
  clearSearch: clearSecondarySearch,
} = useTrackSearch({ perPage: 50 })

// Sync local track arrays with track changes/removals
useTrackSync(tracks, { isLibraryList: true })
useTrackSync(friendsTracks)
useTrackSync(globalTracks)

// Fetch function for VirtualTrackList (without search)
const fetchTracks = async ({ offset, limit }) => {
  const response = await api.get('/tracks', {
    params: {
      offset,
      limit,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }
  })
  return response.data
}

// Handle click from VirtualTrackList
const handleVirtualClick = ({ track, index, allTracks }) => {
  playerStore.playTrack(track, allTracks)
}

// Handle menu from VirtualTrackList  
const handleVirtualMenu = ({ track, index, event }) => {
  openMenu('track', track, 'library', event)
}

const loadSearchTracks = async () => {
  loading.value = true
  try {
    await libraryStore.fetchTracks({
      page: page.value,
      per_page: perPage,
      search: props.searchQuery || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    })
    
    // If we're on page 1, replace. If not, append.
    // Actually current logic in LibraryView was replace on search/sort, append on loadMore.
    // libraryStore.tracks contains the result of fetchTracks (which might be just page)
    // Wait, let's check existing implementation.
    // Existing: tracks.value = libraryStore.tracks
    // But loadMore does: page++ -> loadTracks.
    // If store replaces content, then we lose previous pages if we don't append locally.
    // Let's check LibraryStore.
    // Assuming LibraryStore stores current response.
    // The current implementation in LibraryView does:
    // tracks.value = libraryStore.tracks
    // This implies libraryStore.tracks is *accumulated* or I missed something.
    // In loadMore: page.value++ -> loadTracks().
    // If libraryStore.fetchTracks replaces the state, then `tracks.value = libraryStore.tracks` would only show the new page.
    // BUT, usually fetchTracks appends if page > 1 or it returns just the new items.
    // Checking `tracks.value < total.value` implies we rely on local `tracks`.
    // Let's double check `LibraryView.vue` logic.
    // It relies on `libraryStore.tracks`.
    // If `libraryStore` accumulates, then we are fine.
    
    // But `loadMore` calls `loadTracks`.
    // I will assume libraryStore.tracks returns the fetched list.
    // IF page > 1, we should probably APPEND.
    // BUT `LibraryView.vue` says `tracks.value = libraryStore.tracks`.
    // This looks like pagination where `tracks` is just the *current* list? 
    // Wait, `hasMore` checks `tracks.value.length < total.value`.
    // If `tracks` is only 50 items (page 2), asking if 50 < 1000 is true.
    // If I show only 50 items, but I want infinite scroll...
    // Infinite scroll usually appends.
    // If `LibraryStore` doesn't append, then `LibraryView.vue` logic `tracks.value = libraryStore.tracks` would replace the list.
    // This means the current implementation IS paginated but using "Load More" button?
    // If so, clicking "Load More" replaces the content with the next page? That's weird for a list that says "Load More".
    // "Load More" usually implies "Add to bottom".
    // I will check `stores/library.js` if possible, but for now I will assume I need to handle appending if the store doesn't.
    // Actually, I'll stick to the exact logic of `LibraryView.vue` to not break it.
    // Code: `await libraryStore.fetchTracks(...)` then `tracks.value = libraryStore.tracks`.
    tracks.value = libraryStore.tracks
    searchTotal.value = libraryStore.total
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = async () => {
  if (loadingMore.value || loading.value || !hasMore.value) return
  loadingMore.value = true
  page.value++
  await loadSearchTracks()
}

const findScrollContainer = (el) => {
  let parent = el?.parentElement
  while (parent) {
    const style = window.getComputedStyle(parent)
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
      return parent
    }
    parent = parent.parentElement
  }
  return window
}

// Setup IntersectionObserver for infinite scroll
const setupObserver = () => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
  
  if (!loadTriggerRef.value) return

  const container = findScrollContainer(loadTriggerRef.value)
  const isWindow = container === window
  
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value && !loading.value && !loadingMore.value) {
        loadMore()
      }
    },
    {
      root: isWindow ? null : container,
      rootMargin: '300px'
    }
  )
  
  observer.observe(loadTriggerRef.value)
}

// Watch loadTriggerRef to setup observer when element appears
watch(loadTriggerRef, (el) => {
  if (el) setupObserver()
})

// Watch searchQuery prop
watch(() => props.searchQuery, async (newVal) => {
  // If query changes, reset page
  page.value = 1
  
  if (newVal) {
    // Search mode - load tracks via library store
    await loadSearchTracks()
    // Search friends + global via unified composable
    await searchFriendsAndGlobal(newVal, tracks.value)
  } else {
    // No search - reset to virtual list mode
    tracks.value = []
    clearSecondarySearch()
    // Reset virtual list
    if (virtualTrackListRef.value) {
      virtualTrackListRef.value.reset()
    }
  }
})

// Like track
const handleLikeTrack = async (track) => {
  if (!track?.id) return
  const current = track.is_liked === true
  track.is_liked = !current
}

const playTrack = (track) => {
  playerStore.playTrack(track, tracks.value)
}

// Play track from friends results (combine all lists for queue)
const playFriendsTrack = (track) => {
  const allTracks = [...tracks.value, ...friendsTracks.value, ...globalTracks.value]
  playerStore.playTrack(track, allTracks)
}

// Play track from global results (combine all lists for queue)
const playGlobalTrack = (track) => {
  const allTracks = [...tracks.value, ...friendsTracks.value, ...globalTracks.value]
  playerStore.playTrack(track, allTracks)
}

// Add track from global/friends library to user's library
const handleAddToLibrary = async (track) => {
  const success = await libraryStore.addToLibrary(track.id)
  if (success) {
    // Update the track in friendsTracks or globalTracks to show it's now in library
    const friendsIdx = friendsTracks.value.findIndex(t => t.id === track.id)
    if (friendsIdx !== -1) {
      friendsTracks.value[friendsIdx].in_library = true
      tracks.value.unshift({ ...friendsTracks.value[friendsIdx], in_library: true })
      friendsTracks.value.splice(friendsIdx, 1)
    }
    
    const globalIdx = globalTracks.value.findIndex(t => t.id === track.id)
    if (globalIdx !== -1) {
      globalTracks.value[globalIdx].in_library = true
      tracks.value.unshift({ ...globalTracks.value[globalIdx], in_library: true })
      globalTracks.value.splice(globalIdx, 1)
    }
    
    uiStore.toast.success('Добавлено', 'Трек добавлен в библиотеку')
  }
}

// Shuffle all library tracks using lazy loading
const shuffleAll = async () => {
  if (shuffling.value) return
  shuffling.value = true
  try {
    const trimmedQuery = props.searchQuery ? props.searchQuery.trim() : ''
    if (trimmedQuery && !searchTotal.value && (friendsTracks.value.length || globalTracks.value.length)) {
      const allSearchTracks = [...friendsTracks.value, ...globalTracks.value]
      if (allSearchTracks.length > 0) {
        const shuffled = [...allSearchTracks]
        for (let i = shuffled.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1))
          ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
        }
        playerStore.playTrack(shuffled[0], shuffled)
      }
    } else {
      await playerStore.playShuffleAll('library', null, null, {
        search: trimmedQuery || undefined
      })
    }
  } finally {
    shuffling.value = false
  }
}

onMounted(() => {
  // VirtualTrackList handles initial load automatically
  // Only need observer for search mode
})

onUnmounted(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
/* Reuse existing styles */
.library-tracks {
  padding-bottom: 20px;
}

/* Virtual tracks section for Spotify-style scrolling */
.virtual-tracks-section {
  min-height: 200px;
}

/* Search results section */
.search-results {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sort-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 16px;
}

/* Loading state - uses .spinner from design-system.css */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--c-text-2);
}

/* Section header styling */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px 10px;
  margin-top: 8px;
  user-select: none;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--c-text-1, #fff);
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-count {
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-3, rgba(255, 255, 255, 0.5));
}

/* Section modifiers for search results */
.section-header.global-section,
.section-header.friends-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--c-bg-4, rgba(255, 255, 255, 0.08));
}

.global-loading {
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
  background: var(--c-bg-3, rgba(255, 255, 255, 0.05));
  color: var(--c-accent, #10b981);
  border: 1px solid var(--c-bg-4, rgba(255, 255, 255, 0.1));
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.load-more-btn:hover {
  background: var(--bg-hover, rgba(255, 255, 255, 0.08));
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.load-trigger {
  min-height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
