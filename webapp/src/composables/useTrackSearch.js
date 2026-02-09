/**
 * Unified track search composable
 * Three-tier search: user library → friends → global network
 * Used by EditPlaylistModal and LibraryTracks for consistent search behavior
 */
import { ref, computed, onUnmounted } from 'vue'
import api, { tracksApi, socialApi } from '@/api/client'

/**
 * @param {Object} options
 * @param {number} options.perPage - Results per tier (default: 20)
 * @param {number} options.debounceDelay - Debounce delay ms (default: 300)
 * @returns {Object} Search state and methods
 */
export function useTrackSearch({ perPage = 20, debounceDelay = 300 } = {}) {
  const searchQuery = ref('')
  const libraryResults = ref([])
  const friendsResults = ref([])
  const globalResults = ref([])
  const isSearching = ref(false)
  const isFriendsLoading = ref(false)
  const isGlobalLoading = ref(false)
  let searchTimeout = null

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
      return
    }

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

    // 2) Friends' libraries
    isFriendsLoading.value = true
    try {
      const friendsRes = await socialApi.searchFriends(query, perPage)
      const friendsItems = friendsRes.data.items || []
      const libraryIds = new Set(libraryResults.value.map(t => t.id))
      friendsResults.value = friendsItems.filter(t => !libraryIds.has(t.id))
    } catch (error) {
      console.error('Failed to search friends:', error)
      friendsResults.value = []
    } finally {
      isFriendsLoading.value = false
    }

    // 3) Global network
    isGlobalLoading.value = true
    try {
      const globalRes = await tracksApi.getGlobal({
        search: query,
        per_page: perPage
      })
      const globalItems = globalRes.data.items || []
      const libraryIds = new Set(libraryResults.value.map(t => t.id))
      const friendsIds = new Set(friendsResults.value.map(t => t.id))
      globalResults.value = globalItems.filter(
        t => !libraryIds.has(t.id) && !friendsIds.has(t.id)
      )
    } catch (error) {
      console.error('Failed to search global:', error)
      globalResults.value = []
    } finally {
      isGlobalLoading.value = false
    }
  }

  const clearSearch = () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    searchQuery.value = ''
    libraryResults.value = []
    friendsResults.value = []
    globalResults.value = []
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
      return
    }

    const libraryIds = new Set(existingLibraryTracks.map(t => t.id))

    // Friends
    isFriendsLoading.value = true
    try {
      const friendsRes = await socialApi.searchFriends(query, perPage)
      const friendsItems = friendsRes.data.items || []
      friendsResults.value = friendsItems.filter(t => !libraryIds.has(t.id))
    } catch (error) {
      console.error('Failed to search friends:', error)
      friendsResults.value = []
    } finally {
      isFriendsLoading.value = false
    }

    // Global
    isGlobalLoading.value = true
    try {
      const globalRes = await tracksApi.getGlobal({ search: query, per_page: perPage })
      const globalItems = globalRes.data.items || []
      const friendsIds = new Set(friendsResults.value.map(t => t.id))
      globalResults.value = globalItems.filter(
        t => !libraryIds.has(t.id) && !friendsIds.has(t.id)
      )
    } catch (error) {
      console.error('Failed to search global:', error)
      globalResults.value = []
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
    hasAnyResults,
    allResults,
    debouncedSearch,
    search,
    searchFriendsAndGlobal,
    clearSearch,
  }
}
