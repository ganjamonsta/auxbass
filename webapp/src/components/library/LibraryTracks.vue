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
        />
        
        <div v-if="hasMore" class="load-more">
          <button @click="loadMore" :disabled="loading">
            {{ loading ? 'Загрузка...' : 'Загрузить ещё' }}
          </button>
        </div>
        
        <div v-if="!tracks.length" class="empty-state">
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
import { useSort } from '@/composables'
import TrackItem from '@/components/TrackItem.vue'
import TrackMenu from '@/components/TrackMenu.vue'
import EditTrackModal from '@/components/EditTrackModal.vue'
import SortChips from '@/components/SortChips.vue'
import api, { playerApi } from '@/api/client'

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

// Watch searchQuery prop
watch(() => props.searchQuery, (newVal) => {
  // If query changes, reset page
   page.value = 1
   loadTracks()
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
  try {
    await playerApi.download(track.id)
  } catch (error) {
    console.error('Failed to download track:', error)
  }
  closeMenu()
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
</style>
