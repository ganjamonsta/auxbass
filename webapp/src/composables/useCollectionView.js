/**
 * useCollectionView composable
 * 
 * Encapsulates common logic for collection view pages:
 * - Debounced search with query/debouncedQuery
 * - reset-view-state event listener (auto-cleanup)
 * - Ref to child component for reset()
 * 
 * Usage:
 *   const { searchQuery, debouncedQuery, search, clear, contentRef } = useCollectionView('/albums')
 *   
 *   <SearchBar v-model="searchQuery" @input="search" />
 *   <LibraryAlbums ref="contentRef" :searchQuery="debouncedQuery" />
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useDebouncedSearch } from './useDebouncedSearch'

/**
 * @param {string} route - Route path to listen for reset events (e.g. '/albums')
 * @param {Function} [onReset] - Optional extra callback on reset
 */
export function useCollectionView(route, onReset = null) {
  const contentRef = ref(null)

  const {
    query: searchQuery,
    debouncedQuery,
    search,
    clear
  } = useDebouncedSearch()

  const handleResetState = (event) => {
    if (event.detail.route === route) {
      clear()
      contentRef.value?.reset()
      onReset?.()
    }
  }

  onMounted(() => {
    window.addEventListener('reset-view-state', handleResetState)
  })

  onUnmounted(() => {
    window.removeEventListener('reset-view-state', handleResetState)
  })

  return {
    searchQuery,
    debouncedQuery,
    search,
    clear,
    contentRef
  }
}
