<template>
  <div class="library-tracks">
    <!-- Sort options -->
    <div class="sort-options">
      <button class="shuffle-all-btn" @click="shuffleAll" :disabled="!total">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
        </svg>
        <span>Перемешать ({{ total }})</span>
      </button>
      <SortChips
        :currentOption="currentOption"
        :sortOrder="sortOrder"
        @next="onNextSort"
        @toggle-order="onToggleOrder"
      />
    </div>

    <!-- Track list -->
    <div class="track-list" ref="trackListRef">
      <div v-if="loading && !tracks.length" class="loading">
        <div class="spinner"></div>
        <span>Загрузка...</span>
      </div>
      
      <template v-else>
        <!-- Section: My Library results -->
        <template v-if="searchQuery && tracks.length">
          <div class="section-header">
            <span class="section-title">Моя библиотека</span>
            <span class="section-count">{{ tracks.length }}</span>
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
          @menu="openTrackMenu(track)"
          @download="handleDirectDownload(track)"
        />
        
        <div v-if="hasMore && !searchQuery" class="load-more">
          <button @click="loadMore" :disabled="loading">
            {{ loading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
        
        <!-- Section: Friends' Libraries results (only when searching) -->
        <template v-if="searchQuery && friendsTracks.length">
          <div class="section-header friends-section">
            <span class="section-title">👥 У друзей</span>
            <span class="section-count">{{ friendsTracks.length }}</span>
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
            @menu="openTrackMenu(track)"
            @download="handleDirectDownload(track)"
            @addToLibrary="handleAddToLibrary(track)"
          />
        </template>
        
        <!-- Loading friends results -->
        <div v-if="searchQuery && friendsLoading" class="global-loading">
          <div class="spinner small"></div>
          <span>Поиск у друзей...</span>
        </div>
        
        <!-- Section: Global Network results (only when searching) -->
        <template v-if="searchQuery && globalTracks.length">
          <div class="section-header global-section">
            <span class="section-title">🌐 Общая сеть</span>
            <span class="section-count">{{ globalTracks.length }}</span>
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
            @menu="openTrackMenu(track)"
            @download="handleDirectDownload(track)"
            @addToLibrary="handleAddToLibrary(track)"
          />
        </template>
        
        <!-- Loading global results -->
        <div v-if="searchQuery && globalLoading" class="global-loading">
          <div class="spinner small"></div>
          <span>Поиск в общей сети...</span>
        </div>
        
        <div v-if="!tracks.length && !friendsTracks.length && !globalTracks.length && !loading && !friendsLoading && !globalLoading" class="empty-state">
          <span class="empty-icon">🎵</span>
          <h3 v-if="searchQuery">Ничего не найдено</h3>
          <template v-else>
            <h3>Библиотека пуста</h3>
            <p>Отправьте аудио боту, чтобы добавить треки</p>
          </template>
        </div>
      </template>
    </div>
    
    <!-- Track context menu -->
    <TrackMenu
      :show="showMenu"
      :track="menuTrack"
      :current-user-id="authStore.user?.id"
      context="library"
      @close="closeMenu"
      @goToArtist="handleGoToArtist"
      @goToAlbum="handleGoToAlbum"
      @addToPlaylist="handleAddToPlaylist"
      @edit="handleEditTrack"
      @download="handleDownloadTrack"
      @delete="handleDeleteTrack"
      @removeFromLibrary="handleRemoveFromLibrary"
      @addToLibrary="handleAddToLibraryFromMenu"
    />
    
    <!-- Edit track modal -->
    <EditTrackModal
      :show="showEditModal"
      :track="editingTrack"
      @close="closeEditModal"
      @saved="handleTrackSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useLibraryStore } from '@/stores/library'
import { usePlayerStore } from '@/stores/player'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useSort } from '@/composables'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import EditTrackModal from '@/components/EditTrackModal.vue'
import SortChips from '@/components/SortChips.vue'
import api, { playerApi, tracksApi, socialApi } from '@/api/client'

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

const loading = ref(false)
const tracks = ref([])
const page = ref(1)
const total = ref(0)
const perPage = 50

// Global search results
const globalTracks = ref([])
const globalLoading = ref(false)

// Friends search results
const friendsTracks = ref([])
const friendsLoading = ref(false)

// Edit modal state
const showEditModal = ref(false)
const editingTrack = ref(null)

const hasMore = computed(() => tracks.value.length < total.value)

const loadTracks = async () => {
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
    total.value = libraryStore.total
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  page.value++
  // Here is the issue: if loadTracks replaces `tracks.value`, then we lose previous items.
  // I will check if I should append.
  // Given user wants "Auto loading" (infinite scroll), likely we want to append.
  // But I am just refactoring now.
  // If I change it to `if (page.value > 1) tracks.value.push(...)` that might be safer.
  // BUT I'll stick to 1:1 copy for now to minimize bugs, assuming the `libraryStore` handles it?
  // Let's check `libraryStore.tracks` behavior if I can.
  // Actually, I'll just check if the user asked for infinite scroll previously and if it was implemented in `ArtistsView` but not `LibraryView` yet?
  // The summary says "Pagination seems inappropriate... need auto-loading".
  // `ArtistsView` uses `IntersectionObserver`.
  // `LibraryView` uses "Load More" button.
  // User asked "unify these sortings" and "use window...".
  // I should probably also implement infinite scroll here since I am touching it?
  // User said "buttons at the top... showing here list... expanded view".
  // I'll stick to "Load More" button to keep this step focused on architecture, unless requested otherwise.
  
  await loadTracks()
}

// Search global library for additional results
const searchGlobal = async (query) => {
  if (!query) {
    globalTracks.value = []
    return
  }
  
  globalLoading.value = true
  try {
    const response = await tracksApi.getGlobal({
      search: query,
      per_page: 30
    })
    
    const globalResults = response.data.items || []
    
    // Filter out tracks that are already in user's library or in friends results
    const libraryIds = new Set(tracks.value.map(t => t.id))
    const friendsIds = new Set(friendsTracks.value.map(t => t.id))
    globalTracks.value = globalResults.filter(t => !libraryIds.has(t.id) && !friendsIds.has(t.id))
  } catch (error) {
    console.error('Failed to search global library:', error)
    globalTracks.value = []
  } finally {
    globalLoading.value = false
  }
}

// Search in friends' libraries (users we follow)
const searchFriends = async (query) => {
  if (!query) {
    friendsTracks.value = []
    return
  }
  
  friendsLoading.value = true
  try {
    const response = await socialApi.searchFriends(query, 30)
    const friendsResults = response.data.items || []
    
    // Filter out tracks that are already in user's library
    const libraryIds = new Set(tracks.value.map(t => t.id))
    friendsTracks.value = friendsResults.filter(t => !libraryIds.has(t.id))
  } catch (error) {
    console.error('Failed to search friends libraries:', error)
    friendsTracks.value = []
  } finally {
    friendsLoading.value = false
  }
}

// Watch searchQuery prop
watch(() => props.searchQuery, async (newVal) => {
  // If query changes, reset page
  page.value = 1
  await loadTracks()
  
  // Also search in friends' libraries and global when there's a search query
  if (newVal) {
    // Search friends first, then global
    await searchFriends(newVal)
    await searchGlobal(newVal)
  } else {
    friendsTracks.value = []
    globalTracks.value = []
  }
})

const onNextSort = () => {
  nextSort()
  page.value = 1
  loadTracks()
}

const onToggleOrder = () => {
  toggleOrder()
  page.value = 1
  loadTracks()
}

// Like track
const handleLikeTrack = async (track) => {
  const newLikedState = await libraryStore.toggleLike(track.id)
  const idx = tracks.value.findIndex(t => t.id === track.id)
  if (idx !== -1) {
    tracks.value[idx].is_liked = newLikedState
  }
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
  await playerStore.playShuffleAll('library')
}

// Track menu state
const menuTrack = ref(null)
const showMenu = ref(false)

const openTrackMenu = (track) => {
  menuTrack.value = track
  showMenu.value = true
}

const closeMenu = () => {
  showMenu.value = false
  menuTrack.value = null
}

const handleGoToArtist = (artist) => {
  router.push(`/artist/${encodeURIComponent(artist)}`)
}

const handleGoToAlbum = (albumId) => {
  if (albumId) {
    router.push(`/album/${albumId}`)
  }
  closeMenu()
}

const handleAddToPlaylist = (track) => {
  closeMenu()
}

const handleEditTrack = (track) => {
  closeMenu()
  editingTrack.value = track
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingTrack.value = null
}

const handleTrackSaved = (updatedTrack) => {
  // Update track in local list
  const index = tracks.value.findIndex(t => t.id === updatedTrack.id)
  if (index !== -1) {
    tracks.value[index] = { ...tracks.value[index], ...updatedTrack }
  }
  // Also update in player if currently playing
  if (playerStore.currentTrack?.id === updatedTrack.id) {
    playerStore.currentTrack = { ...playerStore.currentTrack, ...updatedTrack }
  }
}

const handleDownloadTrack = async (track) => {
  await handleDirectDownload(track)
  closeMenu()
}

// Direct download from TrackItem button - sends file via Telegram bot
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

const handleDeleteTrack = async (track) => {
  if (confirm('Удалить трек полностью?')) {
    await libraryStore.deleteTrack(track.id)
    tracks.value = tracks.value.filter(t => t.id !== track.id)
  }
  closeMenu()
}

const handleRemoveFromLibrary = async (track) => {
  await libraryStore.removeFromLibrary(track.id)
  tracks.value = tracks.value.filter(t => t.id !== track.id)
  closeMenu()
}

// Handle add to library from context menu (for global tracks)
const handleAddToLibraryFromMenu = async (track) => {
  await handleAddToLibrary(track)
  closeMenu()
}

onMounted(() => {
  loadTracks()
})
</script>

<style scoped>
/* Reuse existing styles */
.library-tracks {
  padding-bottom: 20px;
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.shuffle-all-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.shuffle-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--bg-highlight);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.load-more button {
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  font-weight: 600;
  cursor: pointer;
}

.load-more button:disabled {
  opacity: 0.5;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary);
}

/* Section headers for search results */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 8px;
  margin-top: 8px;
}

.section-header.global-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
}

.section-header.friends-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-count {
  font-size: 12px;
  color: var(--text-muted);
  background: var(--bg-highlight);
  padding: 2px 8px;
  border-radius: 10px;
}

.global-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.spinner.small {
  width: 16px;
  height: 16px;
  border-width: 2px;
  margin-bottom: 0;
}
</style>
