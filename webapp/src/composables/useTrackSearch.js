/**
 * Track search composable
 * Handles debounced track search in library and global
 */
import { ref } from 'vue'
import api from '@/api/client'

export function useTrackSearch() {
  const searchQuery = ref('')
  const searchResults = ref([])
  const isSearching = ref(false)
  let searchTimeout = null

  const debouncedSearch = (delay = 300) => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchTimeout = setTimeout(() => {
      search()
    }, delay)
  }

  const search = async () => {
    if (!searchQuery.value.trim()) {
      searchResults.value = []
      return
    }

    isSearching.value = true
    try {
      // Search in personal library first
      const libraryResponse = await api.get('/library', {
        params: {
          search: searchQuery.value,
          per_page: 20
        }
      })
      const libraryTracks = libraryResponse.data.items || []

      // Then search in global library
      const globalResponse = await api.get('/tracks/global', {
        params: {
          search: searchQuery.value,
          per_page: 20
        }
      })
      const globalTracks = globalResponse.data.items || []

      // Merge results, avoiding duplicates (by track id)
      const seenIds = new Set(libraryTracks.map(t => t.id))
      const uniqueGlobalTracks = globalTracks.filter(t => !seenIds.has(t.id))

      searchResults.value = [...libraryTracks, ...uniqueGlobalTracks].slice(0, 30)
    } catch (error) {
      console.error('Failed to search tracks:', error)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  const clearSearch = () => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchQuery.value = ''
    searchResults.value = []
  }

  return {
    searchQuery,
    searchResults,
    isSearching,
    debouncedSearch,
    search,
    clearSearch
  }
}
