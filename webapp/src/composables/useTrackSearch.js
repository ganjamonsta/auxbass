/**
 * Unified track search composable
 * Three-tier search: user library → friends → global network
 * Used by EditPlaylistModal and LibraryTracks for consistent search behavior
 */
import { ref, computed, onUnmounted } from 'vue'
import api, { tracksApi, socialApi } from '@/api/client'

/**
 * @param {Object} options
 * @param {number} options.perPage - Results per tier (default: 50)
 * @param {number} options.debounceDelay - Debounce delay ms (default: 300)
 * @returns {Object} Search state and methods
 */
export function useTrackSearch({ perPage = 50, debounceDelay = 300 } = {}) {
  const searchQuery = ref('')
  const libraryResults = ref([])
  const friendsResults = ref([])
  const globalResults = ref([])
  const isSearching = ref(false)
  const isFriendsLoading = ref(false)
  const isGlobalLoading = ref(false)
  let searchTimeout = null

  // Pagination state for friends/global
  const friendsPage = ref(1)
  const friendsTotal = ref(0)
  const globalPage = ref(1)
  const globalTotal = ref(0)
  const isFriendsLoadingMore = ref(false)
  const isGlobalLoadingMore = ref(false)

  // Current query and dedup set (cached for loadMore)
  let _currentQuery = ''
  let _libraryIds = new Set()

  const hasMoreFriends = computed(() => friendsResults.value.length < friendsTotal.value)
  const hasMoreGlobal = computed(() => globalResults.value.length < globalTotal.value)

  const hasAnyResults = computed(() =>
    libraryResults.value.length > 0 ||
    friendsResults.value.length > 0 ||
    globalResults.value.length > 0
  )

  /** Flat merged list (library first, then friends, then global) — for simple consumers */
  const allResults = computed(() => [
    ...libraryResults.value,
    ...friendsResults.value,
    ...globalResults.value,
  ])

  const debouncedSearch = () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(search, debounceDelay)
  }

  const search = async () => {
    const query = searchQuery.value.trim()
    if (!query) {
      libraryResults.value = []
      friendsResults.value = []
      globalResults.value = []
      friendsTotal.value = 0
      globalTotal.value = 0
      return
    }

    _currentQuery = query

    // 1) User's library
    isSearching.value = true
    try {
      const libraryRes = await api.get('/library', {
        params: { search: query, per_page: perPage }
      })
      libraryResults.value = libraryRes.data.items || []
    } catch (error) {
      console.error('Failed to search library:', error)
      libraryResults.value = []
    } finally {
      isSearching.value = false
    }

    _libraryIds = new Set(libraryResults.value.map(t => t.id))

    // 2) Friends' libraries
    friendsPage.value = 1
    isFriendsLoading.value = true
    try {
      const friendsRes = await socialApi.searchFriends(query, perPage, 1)
      const friendsItems = friendsRes.data.items || []
      friendsTotal.value = friendsRes.data.total || 0
      friendsResults.value = friendsItems.filter(t => !_libraryIds.has(t.id))
    } catch (error) {
      console.error('Failed to search friends:', error)
      friendsResults.value = []
      friendsTotal.value = 0
    } finally {
      isFriendsLoading.value = false
    }

    // 3) Global network
    globalPage.value = 1
    isGlobalLoading.value = true
    try {
      const globalRes = await tracksApi.getGlobal({
        search: query,
        per_page: perPage,
        page: 1
      })
      const globalItems = globalRes.data.items || []
      globalTotal.value = globalRes.data.total || 0
      const friendsIds = new Set(friendsResults.value.map(t => t.id))
      globalResults.value = globalItems.filter(
        t => !_libraryIds.has(t.id) && !friendsIds.has(t.id)
      )
    } catch (error) {
      console.error('Failed to search global:', error)
      globalResults.value = []
      globalTotal.value = 0
    } finally {
      isGlobalLoading.value = false
    }
  }

  /** Load more friends results */
  const loadMoreFriends = async () => {
    if (!hasMoreFriends.value || isFriendsLoadingMore.value || !_currentQuery) return
    isFriendsLoadingMore.value = true
    try {
      friendsPage.value++
      const friendsRes = await socialApi.searchFriends(_currentQuery, perPage, friendsPage.value)
      const newItems = (friendsRes.data.items || []).filter(t => !_libraryIds.has(t.id))
      friendsResults.value = [...friendsResults.value, ...newItems]
      friendsTotal.value = friendsRes.data.total || friendsTotal.value
    } catch (error) {
      console.error('Failed to load more friends:', error)
      friendsPage.value--
    } finally {
      isFriendsLoadingMore.value = false
    }
  }

  /** Load more global results */
  const loadMoreGlobal = async () => {
    if (!hasMoreGlobal.value || isGlobalLoadingMore.value || !_currentQuery) return
    isGlobalLoadingMore.value = true
    try {
      globalPage.value++
      const globalRes = await tracksApi.getGlobal({
        search: _currentQuery,
        per_page: perPage,
        page: globalPage.value
      })
      const friendsIds = new Set(friendsResults.value.map(t => t.id))
      const newItems = (globalRes.data.items || []).filter(
        t => !_libraryIds.has(t.id) && !friendsIds.has(t.id)
      )
      globalResults.value = [...globalResults.value, ...newItems]
      globalTotal.value = globalRes.data.total || globalTotal.value
    } catch (error) {
      console.error('Failed to load more global:', error)
      globalPage.value--
    } finally {
      isGlobalLoadingMore.value = false
    }
  }

  const clearSearch = () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    searchQuery.value = ''
    libraryResults.value = []
    friendsResults.value = []
    globalResults.value = []
    friendsTotal.value = 0
    globalTotal.value = 0
    friendsPage.value = 1
    globalPage.value = 1
    _currentQuery = ''
    _libraryIds = new Set()
  }

  /**
   * Search only friends + global tiers (for consumers that manage their own library search).
   * Deduplicates against provided library track IDs.
   * @param {string} query - Search query
   * @param {Array} existingLibraryTracks - Library results to deduplicate against
   */
  const searchFriendsAndGlobal = async (query, existingLibraryTracks = []) => {
    if (!query) {
      friendsResults.value = []
      globalResults.value = []
      friendsTotal.value = 0
      globalTotal.value = 0
      return
    }

    _currentQuery = query
    _libraryIds = new Set(existingLibraryTracks.map(t => t.id))

    // Friends
    friendsPage.value = 1
    isFriendsLoading.value = true
    try {
      const friendsRes = await socialApi.searchFriends(query, perPage, 1)
      const friendsItems = friendsRes.data.items || []
      friendsTotal.value = friendsRes.data.total || 0
      friendsResults.value = friendsItems.filter(t => !_libraryIds.has(t.id))
    } catch (error) {
      console.error('Failed to search friends:', error)
      friendsResults.value = []
      friendsTotal.value = 0
    } finally {
      isFriendsLoading.value = false
    }

    // Global
    globalPage.value = 1
    isGlobalLoading.value = true
    try {
      const globalRes = await tracksApi.getGlobal({ search: query, per_page: perPage, page: 1 })
      const globalItems = globalRes.data.items || []
      globalTotal.value = globalRes.data.total || 0
      const friendsIds = new Set(friendsResults.value.map(t => t.id))
      globalResults.value = globalItems.filter(
        t => !_libraryIds.has(t.id) && !friendsIds.has(t.id)
      )
    } catch (error) {
      console.error('Failed to search global:', error)
      globalResults.value = []
      globalTotal.value = 0
    } finally {
      isGlobalLoading.value = false
    }
  }

  onUnmounted(() => {
    if (searchTimeout) clearTimeout(searchTimeout)
  })

  return {
    searchQuery,
    libraryResults,
    friendsResults,
    globalResults,
    isSearching,
    isFriendsLoading,
    isGlobalLoading,
    isFriendsLoadingMore,
    isGlobalLoadingMore,
    hasMoreFriends,
    hasMoreGlobal,
    friendsTotal,
    globalTotal,
    hasAnyResults,
    allResults,
    debouncedSearch,
    search,
    searchFriendsAndGlobal,
    loadMoreFriends,
    loadMoreGlobal,
    clearSearch,
  }
}
